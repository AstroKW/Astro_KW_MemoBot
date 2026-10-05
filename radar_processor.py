import os
import re
import sqlite3
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
DB_NAME = "memobot.db"

STOP_WORDS_IT = {
    "a", "ad", "al", "allo", "ai", "agli", "all", "alla", "alle", "con", "col", "coi",
    "da", "dal", "dallo", "dai", "dagli", "dall", "dalla", "dalle", "di", "del", "dello",
    "dei", "degli", "dell", "della", "delle", "in", "nel", "nello", "nei", "negli",
    "nell", "nella", "nelle", "su", "sul", "sullo", "sui", "sugli", "sull", "sulla",
    "sulle", "per", "tra", "fra", "il", "lo", "la", "i", "gli", "le", "l", "un", "uno",
    "una", "un'", "e", "ed", "o", "od", "ma", "se", "perché", "come", "cosa", "chi",
    "dove", "quando", "quanto", "quale", "quali", "che", "cui", "non", "più", "molto",
    "poco", "anche", "ancora", "già", "poi", "dopo", "prima", "mio", "mia", "miei",
    "mie", "tuo", "tua", "tuoi", "tue", "suo", "sua", "suoi", "sue", "nostro", "nostra",
    "nostri", "nostre", "vostro", "vostra", "vostri", "vostre", "loro", "questo",
    "questa", "questi", "queste", "quello", "quella", "quelli", "quelle", "tutto",
    "tutti", "tutta", "tutte", "ho", "hai", "ha", "abbiamo", "avete", "hanno", "sono",
    "sei", "è", "siamo", "siete", "era", "erano", "stato", "stata", "stati", "state",
    "fare", "fatto", "memo", "appunto", "appunti", "note", "nota", "trova", "cerca",
    "dimmi", "mostrami", "fammi"
}

def stem_italiano(parola: str) -> str:
    """
    Restituisce la radice morfologica di base (stem) di una parola italiana
    per consentire il matching tra singolari, plurali e forme flesse (es. libri -> libr, libro -> libr).
    Non richiede librerie esterne.
    """
    p = parola.lower().strip()
    if len(p) <= 3:
        return p
    
    # Rimuovi suffissi lunghi se lasciano una radice di almeno 4 lettere
    suffissi_lunghi = ["amente", "azione", "azioni", "atore", "atori", "atrice", "atrici", "mento", "menti", "ibile", "ibili", "abile", "abili"]
    for s in suffissi_lunghi:
        if p.endswith(s) and len(p) - len(s) >= 4:
            p = p[:-len(s)]
            break

    # Rimuovi desinenze participiali o verbali comuni
    suffissi_medi = ["ando", "endo", "asse", "assi", "ammo", "este", "esti", "etta", "ette", "etti", "etto"]
    for s in suffissi_medi:
        if p.endswith(s) and len(p) - len(s) >= 4:
            p = p[:-len(s)]
            break

    # Rimuovi desinenze nominali/aggettivali singolari/plurali (-o, -a, -i, -e)
    # se la parola risultante ha almeno 3 caratteri (es. libro/libri -> libr, cane/cani -> can)
    if len(p) >= 4 and p[-1] in ('o', 'a', 'i', 'e'):
        p = p[:-1]
        
    return p

def estrai_parole_chiave(testo: str) -> list[tuple[str, str]]:
    """Estrae coppie (parola, stem) significative dal testo della domanda utente."""
    if not testo:
        return []
    parole = re.findall(r'\b[a-zA-Zàèéìòù0-9_-]{3,}\b', testo.lower())
    risultato = []
    for p in parole:
        if p not in STOP_WORDS_IT:
            risultato.append((p, stem_italiano(p)))
    return risultato

def cerca_memo_rilevanti(query_utente: str, limite: int = 15, categoria_filtro: str = None) -> list[dict]:
    """
    Recupera i memo più rilevanti dal database SQLite combinando:
    - Parole chiave esatte e matching morfologico (stemming italiano per singolari/plurali)
    - Intenti specifici (urgenza P1/P2, scadenze promemoria, categorie)
    - Inclusione intelligente del Cestino (come salvagente per ricerche di note specifiche)
    - Bonus per priorità e recency
    """
    if not os.path.exists(DB_NAME):
        return []
        
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Carichiamo tutti i memo (anche cestinati) per dare a Radar la massima visione d'insieme
    query_base = "SELECT * FROM memo"
    params = []
    
    if categoria_filtro and categoria_filtro != "Tutte le categorie":
        query_base += " WHERE categoria = ?"
        params.append(categoria_filtro)
        
    query_base += " ORDER BY data_creazione DESC"
    cursor.execute(query_base, tuple(params))
    tutti_i_memo = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not tutti_i_memo:
        return []
        
    coppie_chiave = estrai_parole_chiave(query_utente)
    query_lower = query_utente.lower()
    
    # Rilevamento intenti speciali nella query
    cerca_urgenza = any(w in query_lower for w in ["urgente", "urgenti", "importante", "p1", "priorità alta", "massima priorità"])
    cerca_scadenze = any(w in query_lower for w in ["scadenza", "scadenze", "promemoria", "calendario", "quando", "oggi", "domani", "settimana", "data", "orario"])
    
    punteggi = []
    for m in tutti_i_memo:
        score = 0
        is_trashed = int(m.get('cestinato', 0)) == 1
        is_archived = int(m.get('archiviato', 0)) == 1
        
        # Se la domanda è prettamente operativa/agenda/urgenze, i memo cestinati vengono ignorati
        if (cerca_urgenza or cerca_scadenze) and is_trashed:
            punteggi.append((0, m))
            continue

        titolo_l = (m.get("titolo") or "").lower()
        riassunto_l = (m.get("riassunto") or "").lower()
        testo_l = (m.get("testo_originale") or "").lower()
        tags_l = (m.get("tags") or "").lower()
        cat_l = (m.get("categoria") or "").lower()
        prio = m.get("priorita", 3)
        promemoria = m.get("data_promemoria")
        
        # Punteggio per parole chiave (match esatto e match di radice/stem)
        for pk, stem in coppie_chiave:
            # Titolo
            if pk in titolo_l:
                score += 10
            elif stem in titolo_l:
                score += 8
                
            # Categoria
            if pk in cat_l:
                score += 6
            elif stem in cat_l:
                score += 5
                
            # Tags
            if pk in tags_l:
                score += 6
            elif stem in tags_l:
                score += 5
                
            # Riassunto
            if pk in riassunto_l:
                score += 5
            elif stem in riassunto_l:
                score += 4
                
            # Testo originale
            if pk in testo_l:
                score += 3
            elif stem in testo_l:
                score += 2
                
        # Bonus per intento urgenza (solo memo non cestinati)
        if cerca_urgenza and not is_trashed:
            if prio == 1:
                score += 15
            elif prio == 2:
                score += 8
                
        # Bonus per intento scadenze (solo memo non cestinati)
        if cerca_scadenze and promemoria and not is_trashed:
            score += 12
            
        # Piccolo bonus standard di priorità
        if prio == 1 and not is_trashed:
            score += 2
        elif prio == 2 and not is_trashed:
            score += 1
            
        # Se il memo è nel cestino ed è stato trovato per parola chiave,
        # applichiamo una moderazione per dare precedenza alle note attive/archiviate
        if is_trashed and score > 0:
            score = int(score * 0.75)
            
        punteggi.append((score, m))
        
    punteggi_validi = [item for item in punteggi if item[0] > 0]
    if punteggi_validi:
        punteggi_validi.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in punteggi_validi[:limite]]
    else:
        # Se nessuna parola chiave combacia, restituisci i più recenti escludendo il cestino
        memo_attivi_o_arch = [m for m in tutti_i_memo if int(m.get('cestinato', 0)) == 0]
        return memo_attivi_o_arch[:limite]

def costruisci_prompt_sistema(memo_selezionati: list[dict]) -> str:
    """Costruisce il system prompt iniettando la data odierna, lo stato, la collocazione e i memo come contesto."""
    giorni_it = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    oggi_dt = datetime.now()
    giorno_oggi_nome = giorni_it[oggi_dt.weekday()]
    oggi_str = f"{oggi_dt.strftime('%Y-%m-%d %H:%M')} ({giorno_oggi_nome})"
    
    contesto_memo = ""
    for m in memo_selezionati:
        prio_val = m.get('priorita', 3)
        prio_str = f"P{prio_val}"
        if prio_val == 1:
            prio_str += " (ALTA/URGENTE)"
        elif prio_val == 2:
            prio_str += " (MEDIA)"
        else:
            prio_str += " (NORMALE)"
            
        scadenza = m.get('data_promemoria') or "Nessuna data di scadenza"
        
        is_trashed = int(m.get('cestinato', 0)) == 1
        is_archived = int(m.get('archiviato', 0)) == 1
        cat_nome = m.get('categoria', 'Altro')
        
        if is_trashed:
            stato_str = "🗑️ CESTINATO (Nel Cestino, scartato/in attesa di eliminazione definitiva)"
            dove_si_trova = "Nel '🗑️ Cestino' (scheda Cestino in alto nella dashboard, può essere ripristinato)"
        elif is_archived:
            stato_str = "📦 ARCHIVIATO (Completato, non attivo)"
            dove_si_trova = f"Nella scheda '📦 Archivio' (sotto la categoria '{cat_nome}')"
        else:
            stato_str = "🟢 ATTIVO (Compito vivo/in corso)"
            dove_si_trova = f"Nelle schede attive: scheda '{cat_nome}' o scheda '📑 Tutti'"

        contesto_memo += f"""
---
[MEMO ID: #{m.get('id')}]
- Titolo: {m.get('titolo', 'Senza titolo')}
- Stato: {stato_str}
- Dove si trova nella Dashboard: {dove_si_trova}
- Categoria: {cat_nome}
- Priorità: {prio_str}
- Tipo: {m.get('tipo_contenuto', 'testo')}
- Data Creazione: {m.get('data_creazione', '')}
- Scadenza Promemoria: {scadenza}
- Riassunto: {m.get('riassunto', '')}
- Note/Testo Originale: {m.get('testo_originale', '')}
- Tags: {m.get('tags', '')}
- Link: {m.get('link_originale') or 'Nessun link'}
"""

    prompt = f"""Sei Astro_KW Radar, l'assistente di intelligenza artificiale locale integrato in Astro_KW MemoBot.
La data e ora corrente è: {oggi_str}.

Il tuo scopo è rispondere alle domande dell'utente, aiutarlo a cercare, riassumere, pianificare le giornate e fare collegamenti basandoti sulle sue note e memo personali salvati.

REGOLE CRUCIALI DI COMPORTAMENTO:
1. Rispondi SEMPRE in italiano, con un tono cordiale, chiaro, empatico, agile e ben strutturato (usa elenchi puntati o grassetto per migliorare la leggibilità).
2. Fai riferimento esplicito ed ESAUSTIVO ai memo pertinenti presenti nell'ARCHIVIO MEMO fornito qui sotto. Cita sempre il titolo e l'ID del memo quando fornisci informazioni (es: "Nel memo '#31 - Profilo angolare ottone'..."). Se ci sono più memo che toccano l'argomento richiesto (anche attraverso parole correlate, singolari/plurali o riferimenti nel testo), elencali TUTTI in modo completo, non limitarti al primo trovato!
3. Gestione dello Stato e di "Dove si trova":
   - Quando l'utente chiede dove si trova un appunto o informazioni sulla sua collocazione, indica con precisione il suo Stato e la Scheda in cui è posizionato nell'interfaccia (es: "Si trova nella scheda '📦 Archivio', categoria Cultura/Notizie" oppure "Si trova tra i compiti attivi nella scheda 'Lavoro'").
4. Gestione Speciale del Cestino (Salvagente Cognitivo):
   - I memo con stato "🗑️ CESTINATO" si trovano nel Cestino. Se sono pertinenti alla domanda o ricerca dell'utente, rispondi riportando le informazioni richieste ma AVVISA SEMPRE CHIARAMENTE: "⚠️ Nota: questo memo si trova attualmente nel 🗑️ Cestino (puoi ripristinarlo in qualsiasi momento dalla scheda Cestino se ti serve ancora)".
   - NON includere MAI memo cestinati quando l'utente ti chiede cosa deve fare, compiti urgenti o pianificazione di agende operative.
5. Gestione delle Priorità e Scadenze:
   - I compiti P1 sono URGENTI e prioritari.
   - Considera la data di oggi per calcolare scadenze future o passate.
6. Onestà e Anti-Allucinazione:
   - Se l'utente fa una domanda su un argomento che NON è minimamente presente nell'archivio, rispondi con cortesia spiegando con precisione che non ci sono note registrate su quel tema nel database.
   - Non inventare memo, cifre o scadenze non presenti nel testo fornito.

ARCHIVIO MEMO CONSULTABILE DALL'INTELLIGENZA ARTIFICIALE:
{contesto_memo if contesto_memo.strip() else "[Nessun memo presente nell'archivio per questa ricerca.]"}
"""
    return prompt

def stream_risposta_radar(cronologia_messaggi: list[dict], memo_selezionati: list[dict]):
    """
    Invia la conversazione al provider AI attivo (Ollama o Cloud) in modalità streaming.
    Yielda i token generati in tempo reale.
    """
    import ai_service
    prompt_sistema = costruisci_prompt_sistema(memo_selezionati)
    
    messaggi_ai = [{"role": "system", "content": prompt_sistema}]
    for msg in cronologia_messaggi:
        messaggi_ai.append({
            "role": msg["role"],
            "content": msg["content"]
        })
        
    try:
        stream = ai_service.stream_chat_completion(messages=messaggi_ai)
        for chunk in stream:
            if chunk:
                yield chunk
    except Exception as e:
        errore_str = str(e)
        provider = ai_service.get_provider()
        provider_label = ai_service.get_active_provider_label()
        
        condizioni_offline = [
            "connection refused", "connect", "rifiuto persistente",
            "winerror 10061", "failed to connect", "unreachable"
        ]
        if provider == "ollama" and any(c in errore_str.lower() for c in condizioni_offline):
            yield (
                "⚠️ **Ollama non è raggiungibile o non è avviato.**\n\n"
                "Per chattare con **Astro_KW Radar**, assicurati che il servizio Ollama sia in esecuzione sul tuo computer.\n\n"
                "*Puoi avviare Ollama dal menu Start o digitando `ollama serve` nel terminale.*"
            )
        elif "api_key" in errore_str.lower() or "authentication" in errore_str.lower() or "unauthorized" in errore_str.lower():
            yield (
                f"⚠️ **Errore di autenticazione con {provider_label}:**\n\n"
                "Verifica che la chiave API nel file `.env` sia corretta e attiva."
            )
        else:
            yield f"⚠️ **Si è verificato un errore durante la risposta di Astro_KW Radar ({provider_label}):** `{errore_str}`"

def render_fonti_consultate(fonti: list[dict]):
    """Renderizza l'elenco espandibile delle fonti consultate con badge di stato, collocazione e dettagli completi."""
    if not fonti:
        return
    with st.expander(f"📚 Fonti consultate ({len(fonti)} memo)", expanded=False):
        for f in fonti:
            is_trashed = int(f.get('cestinato', 0)) == 1
            is_archived = int(f.get('archiviato', 0)) == 1
            prio = f.get('priorita', 3)
            cat = f.get('categoria', 'Altro')
            
            if is_trashed:
                badge = "🗑️ [CESTINATO]"
                collocazione = "Scheda 🗑️ Cestino"
            elif is_archived:
                badge = "⚪ [ARCHIVIATO]"
                collocazione = f"Scheda 📦 Archivio ({cat})"
            elif prio == 1:
                badge = "🔴 [P1 - URGENTE]"
                collocazione = f"Scheda {cat}"
            elif prio == 2:
                badge = "🟡 [P2 - MEDIA]"
                collocazione = f"Scheda {cat}"
            else:
                badge = "🟢 [P3]"
                collocazione = f"Scheda {cat}"
                
            titolo = f.get('titolo') or "Senza Titolo"
            memo_id = f.get('id')
            data_creazione = f.get('data_creazione', '')
            
            link_html = f'<p style="margin: 4px 0;">🔗 <b>Link:</b> <a href="{f.get("link_originale")}" target="_blank">{f.get("link_originale")}</a></p>' if f.get('link_originale') else ''
            scadenza_html = f'<p style="margin: 4px 0;">⏰ <b>Promemoria:</b> <code>{f.get("data_promemoria")}</code></p>' if f.get('data_promemoria') else ''
            testo_raw = str(f.get("testo_originale") or "").strip()
            testo_html = f'<p style="margin: 4px 0; font-size:0.88em; opacity:0.85;">📝 <b>Testo originale:</b> {testo_raw[:250]}...</p>' if testo_raw else ''
            
            details_html = f'''
            <details style="margin-bottom: 8px; padding: 6px 12px; background: rgba(128,128,128,0.08); border-radius: 6px; border: 1px solid rgba(128,128,128,0.2);">
                <summary style="cursor: pointer; font-weight: 600;">
                    {badge} <b>#{memo_id}</b> — {titolo} <i>({cat})</i> — <span style="font-size:0.85em; opacity:0.8;">{data_creazione}</span>
                </summary>
                <div style="margin-top: 8px; font-size: 0.92em; line-height: 1.5;">
                    <p style="margin: 4px 0;">📍 <b>Collocazione:</b> <code>{collocazione}</code></p>
                    <p style="margin: 4px 0;">💡 <b>Riassunto:</b> {f.get('riassunto')}</p>
                    {link_html}
                    {scadenza_html}
                    {testo_html}
                </div>
            </details>
            '''
            st.markdown(details_html, unsafe_allow_html=True)

def render_scheda_radar(df_totale=None):
    """Renderizza l'interfaccia interattiva di Astro_KW Radar all'interno di Streamlit."""
    st.markdown("""
    <div style="padding: 10px 0 15px 0;">
        <h2 style="margin: 0; font-size: 1.8rem; font-weight: 700; color: inherit; display: flex; align-items: center; flex-wrap: wrap; gap: 10px;">
            <span>🔭 Astro_KW Radar</span>
            <span style="font-size: 0.85rem; font-weight: 500; padding: 4px 12px; border-radius: 20px; background: rgba(128, 128, 128, 0.15); border: 1px solid rgba(128, 128, 128, 0.25); cursor: help;" title="Chatta con Astro_KW MemoBot">
                💬 Chatta con Astro_KW MemoBot
            </span>
        </h2>
        <p style="margin: 6px 0 0 0; opacity: 0.85; font-size: 1.0rem;">
            Interroga ed esplora il tuo archivio in linguaggio naturale. L'AI locale analizza i tuoi memo per trovare risposte, scadenze e collegamenti in totale riservatezza.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Inizializzazione cronologia chat
    if "radar_chat" not in st.session_state:
        st.session_state.radar_chat = []

    # Barra di controllo e filtri rapidi
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        categorie_opzioni = ["Tutte le categorie", "Lavoro", "Sport", "Tempo Libero", "Famiglia/Personale", "Tecnologia", "Cultura/Notizie", "Spesa/Acquisti", "Altro"]
        filtro_cat = st.selectbox("🎯 Ambito di ricerca:", categorie_opzioni, key="radar_filtro_cat")
    with col2:
        st.write("")
        st.write("")
        solo_p1 = st.checkbox("🔴 Solo P1 Urgenti", key="radar_solo_p1")
    with col3:
        st.write("")
        st.write("")
        if st.button("🧹 Nuova Chat", use_container_width=True, help="Cancella la cronologia corrente della conversazione"):
            st.session_state.radar_chat = []
            st.session_state.radar_pending_query = None
            st.rerun()

    st.markdown("---")

    # Se la chat è vuota, mostriamo suggerimenti rapidi
    if not st.session_state.radar_chat:
        st.info("💡 **Come posso aiutarti?** Puoi farmi domande libere, ad esempio:")
        col_sugg1, col_sugg2, col_sugg3 = st.columns(3)
        with col_sugg1:
            if st.button("🔴 Cosa devo fare di urgente?", use_container_width=True):
                st.session_state.radar_pending_query = "Quali sono i miei compiti o memo più urgenti e prioritari?"
                st.rerun()
        with col_sugg2:
            if st.button("📅 Ho scadenze in arrivo?", use_container_width=True):
                st.session_state.radar_pending_query = "Quali sono le prossime scadenze e promemoria salvati?"
                st.rerun()
        with col_sugg3:
            if st.button("💼 Riassumi i memo di lavoro", use_container_width=True):
                st.session_state.radar_pending_query = "Fammi una sintesi di tutti i memo e appunti di lavoro recenti."
                st.rerun()

    # Visualizzazione della cronologia dei messaggi
    for msg in st.session_state.radar_chat:
        with st.chat_message(msg["role"], avatar="🚀" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])
            if msg.get("fonti"):
                render_fonti_consultate(msg["fonti"])

    # Gestione invio nuova domanda (tramite chat_input o click su suggerimento)
    query_da_inviare = None
    if "radar_pending_query" in st.session_state and st.session_state.radar_pending_query:
        query_da_inviare = st.session_state.radar_pending_query
        st.session_state.radar_pending_query = None
    else:
        chat_input_val = st.chat_input("Chiedi ad Astro_KW Radar (es. 'Cosa mi ricordo su...', 'Organizza i compiti')...")
        if chat_input_val:
            query_da_inviare = chat_input_val

    if query_da_inviare:
        # Aggiunta messaggio utente
        st.session_state.radar_chat.append({"role": "user", "content": query_da_inviare})
        with st.chat_message("user"):
            st.markdown(query_da_inviare)

        # Recupero memo con RAG
        categoria_target = filtro_cat if filtro_cat != "Tutte le categorie" else None
        memo_trovati = cerca_memo_rilevanti(query_da_inviare, limite=12, categoria_filtro=categoria_target)
        if solo_p1:
            memo_trovati = [m for m in memo_trovati if m.get('priorita') == 1]

        # Generazione risposta in streaming
        with st.chat_message("assistant", avatar="🚀"):
            stream_gen = stream_risposta_radar(st.session_state.radar_chat, memo_trovati)
            risposta_completa = st.write_stream(stream_gen)
            if memo_trovati:
                render_fonti_consultate(memo_trovati)

        # Salvataggio risposta assistente con relative fonti
        st.session_state.radar_chat.append({
            "role": "assistant",
            "content": risposta_completa,
            "fonti": memo_trovati
        })
        st.rerun()
