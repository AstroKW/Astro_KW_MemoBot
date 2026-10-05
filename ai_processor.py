import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

# Modello configurabile da .env (default: qwen2.5:14b)
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

CATEGORIE_PERMESSE = [
    "Lavoro",
    "Sport",
    "Tempo Libero",
    "Famiglia/Personale",
    "Tecnologia",
    "Cultura/Notizie",
    "Spesa/Acquisti",
    "Altro"
]

def estrai_priorita_esplicita(testo: str) -> int | None:
    """
    Riconosce se l'utente ha esplicitato una priorità nel messaggio (testo o vocale):
    es. "memo priorità 1", "priorita 1", "p1", "urgente", "#p1", "priorità alta".
    """
    if not testo:
        return None
    testo_lower = testo.lower()
    
    # Priorità 1 (Alta/Urgente)
    if re.search(r'\b(priorit[aà]\s*1|p1|#p1|urgente|alta priorit[aà]|massima priorit[aà])\b', testo_lower):
        return 1
        
    # Priorità 2 (Media)
    if re.search(r'\b(priorit[aà]\s*2|p2|#p2|media priorit[aà])\b', testo_lower):
        return 2
        
    # Priorità 3 (Normale/Bassa)
    if re.search(r'\b(priorit[aà]\s*3|p3|#p3|bassa priorit[aà]|normale priorit[aà])\b', testo_lower):
        return 3
        
    return None

def analizza_testo(testo_input: str, titolo_suggerito: str = "") -> dict:
    """
    Invia il testo ad Ollama e richiede una risposta in formato JSON con:
    - titolo
    - riassunto
    - categoria (scelta dalla lista fissa)
    - priorita (1, 2 o 3)
    - data_promemoria (data/ora ISO o null)
    - tags (lista di parole chiave)
    """
    from datetime import datetime, timedelta
    giorni_it = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    oggi_dt = datetime.now()
    giorno_oggi_nome = giorni_it[oggi_dt.weekday()]
    data_oggi = f"{oggi_dt.strftime('%Y-%m-%d')} ({giorno_oggi_nome})"
    
    # Genera la tabella esatta dei prossimi 7 giorni per eliminare gli errori di calcolo relativo degli LLM
    giorni_prossimi = []
    for delta in range(1, 8):
        dt_succ = oggi_dt + timedelta(days=delta)
        nome_g = giorni_it[dt_succ.weekday()]
        label = "Domani" if delta == 1 else f"{nome_g} prossimo"
        giorni_prossimi.append(f"- {label}: {dt_succ.strftime('%Y-%m-%d')}")
    calendario_riferimento = "\n".join(giorni_prossimi)

    # 1. Controllo se l'utente ha indicato esplicitamente la priorità
    priorita_utente = estrai_priorita_esplicita(testo_input)

    guida_titolo = f'Se presente, puoi ispirarti a questo titolo già estratto: "{titolo_suggerito}".' if titolo_suggerito else 'Crea un titolo chiaro e accattivante.'
    categorie_str = ", ".join(CATEGORIE_PERMESSE)

    prompt = f"""
Sei un assistente per l'organizzazione personale e il riassunto intelligente di memo e note personali.
Oggi è: {data_oggi}.

CALENDARIO DI RIFERIMENTO PER DATE FUTURE:
- Oggi: {oggi_dt.strftime('%Y-%m-%d')} ({giorno_oggi_nome})
{calendario_riferimento}

Analizza il seguente contenuto ed estrai le informazioni chiave in formato JSON.

REGOLE CRUCIALI:
1. Attieniti RIGOROSAMENTE ed ESCLUSIVAMENTE alle informazioni fornite nel testo. NON inventare mai dettagli assenti.
2. CATEGORIA: Assegna OBBLIGATORIAMENTE una sola categoria scelta ESATTAMENTE tra queste:
   [{categorie_str}]
3. PRIORITÀ:
   - 1 = Se riguarda urgenze critiche, scadenze imminenti ("entro oggi/domani"), pagamenti urgenti, appuntamenti importanti.
   - 2 = Se importante ma non imminente (progetti, compiti della settimana).
   - 3 = Se nota informativa generale, lettura/video di svago, ricetta o appunto per il tempo libero.
4. PROMEMORIA E SCADENZE TEMPORALI:
   - Se nel testo viene menzionata una scadenza o giorno (es. "martedì prossimo", "venerdì", "domani", "alle ore dieci"), consulta il CALENDARIO DI RIFERIMENTO sopra riportato per ricavare la data esatta "YYYY-MM-DD" e l'eventuale orario "HH:MM".
   - Se viene menzionato un orario (es. "alle dieci" o "ore dieci" -> 10:00, "alle venti" -> 20:00), formattalo sempre come "YYYY-MM-DD HH:MM".
   - Se NON viene menzionato alcun orario ma solo il giorno, restituisci solo la data "YYYY-MM-DD" senza forzare orari inventati.
   - Se NON ci sono scadenze o date future da ricordare, imposta "data_promemoria": null.
5. Restituisci ESCLUSIVAMENTE un JSON valido con questa struttura:
{{
    "titolo": "Un titolo breve e chiaro (max 8 parole). {guida_titolo}",
    "riassunto": "Un riassunto fedele, scorrevole e sintetico (2-4 frasi basate SOLO sui fatti citati)",
    "categoria": "Una tra quelle indicate",
    "priorita": 1, 2 o 3,
    "data_promemoria": "YYYY-MM-DD HH:MM oppure null",
    "tags": ["tag1", "tag2", "tag3"]
}}

Contenuto da analizzare:
{testo_input}
"""

    try:
        import ai_service
        contenuto_risposta = ai_service.chat_completion(
            messages=[{'role': 'user', 'content': prompt}],
            format_json=True
        )
        
        # Pulizia robusta di eventuali wrapper markdown ```json ... ```
        testo_pulito = re.sub(r'^```(?:json)?\s*', '', contenuto_risposta.strip(), flags=re.IGNORECASE)
        testo_pulito = re.sub(r'\s*```$', '', testo_pulito.strip())
        
        # Estrai la prima porzione JSON valida se ci fosse testo prima o dopo
        match_json = re.search(r'(\{.*\})', testo_pulito, re.DOTALL)
        if match_json:
            testo_pulito = match_json.group(1)
            
        dati = json.loads(testo_pulito)
        
        # Validazione Titolo
        if not dati.get("titolo") and titolo_suggerito:
            dati["titolo"] = titolo_suggerito
            
        # Validazione Categoria
        cat = dati.get("categoria", "").strip()
        if cat not in CATEGORIE_PERMESSE:
            # Cerca corrispondenza parziale o assegna Altro
            match = next((c for c in CATEGORIE_PERMESSE if c.lower() in cat.lower()), "Altro")
            dati["categoria"] = match
            
        # Validazione Priorità (la scelta esplicita dell'utente ha priorità assoluta)
        if priorita_utente is not None:
            dati["priorita"] = priorita_utente
        else:
            try:
                p = int(dati.get("priorita", 3))
                dati["priorita"] = p if p in [1, 2, 3] else 3
            except (ValueError, TypeError):
                dati["priorita"] = 3
                
        # Validazione Tags
        if not isinstance(dati.get("tags"), list):
            dati["tags"] = ["generale"]

        # Validazione Data Promemoria
        dp = dati.get("data_promemoria")
        if dp and str(dp).lower() not in ["null", "none", ""]:
            dati["data_promemoria"] = str(dp).strip()
        else:
            dati["data_promemoria"] = None
            
        return dati

    except Exception as e:
        import ai_service
        print(f"[AI] Errore durante l'elaborazione con {ai_service.get_active_provider_label()}: {e}")
        fallback_titolo = titolo_suggerito if titolo_suggerito else "Memo"
        fallback_priorita = priorita_utente if priorita_utente is not None else 3
        return {
            "titolo": fallback_titolo,
            "riassunto": testo_input[:150] + "...",
            "categoria": "Altro",
            "priorita": fallback_priorita,
            "tags": ["generale"]
        }

if __name__ == "__main__":
    test_1 = "Memo priorità 1: ricordati di pagare la bolletta della luce entro stasera altrimenti scade."
    print("Test priorità esplicita P1...")
    res1 = analizza_testo(test_1)
    print("Risultato 1 (Priorità attesa: 1, Categoria attesa: Spesa/Acquisti o Famiglia/Personale):")
    print(json.dumps(res1, indent=2, ensure_ascii=False))