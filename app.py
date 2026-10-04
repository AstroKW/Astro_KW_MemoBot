import os
import sys
import subprocess
import urllib.parse
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import database
import calendar_sync
import settings_manager
import guida_utente

# Configurazione della pagina con il logo Astro_KW come favicon
LOGO_PATH = "LOGO_TONDO_NERO.png"

st.set_page_config(
    page_title="Astro_KW MemoBot - Archivio Personale",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🧠",
    layout="wide"
)

# Caricamento e iniezione del tema e degli stili di accessibilità (WCAG)
impostazioni = settings_manager.carica_impostazioni()
st.markdown(settings_manager.genera_css_accessibilita(impostazioni), unsafe_allow_html=True)

# Inizializza o migra il DB all'avvio
database.init_db()

def carica_memo():
    """Recupera tutti i memo dal database SQLite."""
    conn = database.get_connection()
    query = "SELECT * FROM memo ORDER BY data_creazione DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        if 'priorita' not in df.columns:
            df['priorita'] = 3
        else:
            df['priorita'] = df['priorita'].fillna(3).astype(int)
            
        if 'categoria' not in df.columns:
            df['categoria'] = 'Altro'
        else:
            df['categoria'] = df['categoria'].fillna('Altro').astype(str)

        if 'data_promemoria' not in df.columns:
            df['data_promemoria'] = None
            
        if 'google_event_id' not in df.columns:
            df['google_event_id'] = None
            
    return df

def genera_link_google_calendar(titolo, data_promemoria_str, testo, link_originale=""):
    """
    Genera un URL per aggiungere l'evento a Google Calendar (predisposto per il calendario FabMemoBot).
    """
    if not data_promemoria_str:
        return None
    try:
        # Pulizia formato data
        data_clean = str(data_promemoria_str).strip()
        if len(data_clean) == 10:  # YYYY-MM-DD
            dt = datetime.strptime(data_clean, "%Y-%m-%d")
            dt_end = dt + timedelta(days=1)
            fmt = "%Y%m%d"
        elif len(data_clean) >= 16:  # YYYY-MM-DD HH:MM
            dt = datetime.strptime(data_clean[:16], "%Y-%m-%d %H:%M")
            dt_end = dt + timedelta(hours=1)
            fmt = "%Y%m%dT%H%M%S"
        else:
            return None

        dates_param = f"{dt.strftime(fmt)}/{dt_end.strftime(fmt)}"
        dettagli = f"{testo}\n\n[Origine: Astro_KW MemoBot]"
        if link_originale:
            dettagli += f"\nLink: {link_originale}"
        dettagli += "\n\n(Calendario consigliato: FabMemoBot)"

        params = {
            "action": "TEMPLATE",
            "text": f"📌 {titolo}",
            "dates": dates_param,
            "details": dettagli
        }
        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
    except Exception:
        return None

# -------------------------------------------------------------
# HEADER CON LOGO E BRANDING ASTRO_KW MEMOBOT
# -------------------------------------------------------------
col_logo, col_titolo = st.columns([0.1, 0.9], vertical_alignment="center")

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=85)
    else:
        st.markdown("## 🚀")

with col_titolo:
    st.markdown("""
        <div style="line-height: 1.15; padding-top: 5px;">
            <h1 style="margin: 0; padding: 0; font-size: 2.3rem; font-weight: 700; color: inherit;">Astro_KW MemoBot</h1>
            <p style="margin: 3px 0 0 0; font-size: 1.15rem; color: inherit; opacity: 0.75; font-weight: 400; letter-spacing: 0.5px;">Archivio personale</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("Consulta, modifica, organizza e sincronizza pensieri, note vocali, screenshot e link raccolti da Telegram.")
st.markdown("---")

df = carica_memo()

# -------------------------------------------------------------
# SIDEBAR: SINCRONIZZAZIONE, RICERCA, FILTRI ED ESPORTAZIONE
# -------------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        c1, c2 = st.columns([0.3, 0.7], vertical_alignment="center")
        with c1:
            st.image(LOGO_PATH, width=50)
        with c2:
            st.markdown("**Astro_KW** MemoBot")
        st.markdown("---")

    # 1. TASTO SINCRONIZZA SUBITO
    st.subheader("⚡ Azioni Rapide")
    if st.button("🔄 Sincronizza ora con Telegram", use_container_width=True, type="primary"):
        with st.spinner("Sincronizzazione messaggi Telegram in corso..."):
            try:
                proc = subprocess.run(
                    [sys.executable, "telegram_sync.py"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                if proc.returncode == 0:
                    st.success("Sincronizzazione completata con successo!")
                    st.rerun()
                else:
                    st.error("Errore durante la sincronizzazione.")
                    st.code(proc.stderr or proc.stdout)
            except Exception as e:
                st.error(f"Errore di avvio sincronizzazione: {e}")

    # Scorciatoie e legenda rapida
    guida_utente.render_quick_cheatsheet_sidebar()

    st.markdown("---")
    st.header("🔍 Ricerca & Filtri")
    
    # 2. Ricerca full-text
    search_query = st.text_input("Cerca parola chiave o titolo:", "")
    
    # 3. Filtro per Priorità
    mappa_priorita = {
        "Tutte le priorità": None,
        "🔴 P1 - Alta / Urgente": 1,
        "🟡 P2 - Media": 2,
        "🟢 P3 - Normale": 3
    }
    priorita_scelta = st.selectbox("Filtra per Priorità:", list(mappa_priorita.keys()))
    priorita_val = mappa_priorita[priorita_scelta]
    
    # 4. Filtro per Tipo Contenuto
    tipi_disponibili = ["Tutti i tipi"] + sorted(list(df['tipo_contenuto'].unique())) if not df.empty else ["Tutti i tipi"]
    tipo_selezionato = st.selectbox("Tipo di contenuto:", tipi_disponibili)

    # 5. Filtro per Tag
    tutti_i_tag = set()
    if not df.empty:
        for tags_str in df['tags'].dropna():
            for tag in tags_str.split(','):
                tag_clean = tag.strip()
                if tag_clean:
                    tutti_i_tag.add(tag_clean)
    
    tag_selezionato = st.selectbox("Filtra per Tag:", ["Tutti i tag"] + sorted(list(tutti_i_tag)))

    # 6. Ordinamento
    st.markdown("---")
    st.subheader("⚙️ Ordinamento")
    ordinamento = st.radio(
        "Ordina memo per:",
        ["🕒 Data (Più recenti)", "⚠️ Priorità (P1 in cima)", "🔤 Titolo (A-Z)"]
    )
    
    # 7. ESPORTAZIONE DATI
    st.markdown("---")
    with st.expander("📥 Esporta Memo"):
        if not df.empty:
            # CSV
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("📄 Scarica CSV (Excel)", data=csv_data, file_name="Astro_KW_MemoBot.csv", mime="text/csv", use_container_width=True)
            
            # JSON
            json_data = df.to_json(orient="records", force_ascii=False, indent=2).encode('utf-8')
            st.download_button("📦 Scarica JSON", data=json_data, file_name="Astro_KW_MemoBot.json", mime="application/json", use_container_width=True)
            
            # Markdown
            md_lines = ["# 🧠 Astro_KW MemoBot — Esportazione Archivio\n\n"]
            for _, r in df.iterrows():
                md_lines.append(f"## {r['titolo']} (P{r['priorita']} | {r['categoria']})\n")
                md_lines.append(f"- **Data:** {r['data_creazione']}\n- **Tipo:** {r['tipo_contenuto']}\n")
                if r['data_promemoria']:
                    md_lines.append(f"- **Promemoria:** {r['data_promemoria']}\n")
                if r['link_originale']:
                    md_lines.append(f"- **Link:** {r['link_originale']}\n")
                md_lines.append(f"\n**Riassunto:** {r['riassunto']}\n\n**Testo originale:**\n{r['testo_originale']}\n\n---\n")
            md_data = "".join(md_lines).encode('utf-8')
            st.download_button("📝 Scarica Markdown", data=md_data, file_name="Astro_KW_MemoBot.md", mime="text/markdown", use_container_width=True)

    # 5. PERSONALIZZAZIONE & ACCESSIBILITÀ (WCAG AAA)
    st.markdown("---")
    with st.expander("🎨 Aspetto & Accessibilità (WCAG)", expanded=False):
        st.caption("Personalizza l'aspetto visivo e attiva funzioni di supporto e leggibilità:")
        
        preset_list = list(settings_manager.PRESETS.keys()) + ["Personalizzato 🛠️"]
        current_preset = impostazioni.get("preset", "Astro Dark (Predefinito)")
        if current_preset not in preset_list:
            current_preset = "Personalizzato 🛠️"
            
        selected_preset = st.selectbox(
            "Tema Visivo:",
            options=preset_list,
            index=preset_list.index(current_preset),
            key="theme_preset_select"
        )
        
        # Se l'utente cambia preset, aggiorniamo i valori attivi di default e riavviamo
        if selected_preset in settings_manager.PRESETS and selected_preset != impostazioni.get("preset"):
            target_preset_values = settings_manager.PRESETS[selected_preset].copy()
            target_preset_values["preset"] = selected_preset
            settings_manager.salva_impostazioni(target_preset_values)
            st.rerun()

        # Tipografia e Lettura
        font_options = ["Inter", "Lexend", "Atkinson Hyperlegible"]
        curr_font = impostazioni.get("font_family", "Inter")
        nuovo_font = st.selectbox(
            "Carattere (Font):", 
            font_options, 
            index=font_options.index(curr_font) if curr_font in font_options else 0,
            help="Atkinson Hyperlegible (Braille Institute) e Lexend offrono la massima leggibilità per ipovedenti o dislessici."
        )
        
        size_options = ["Compatta (90%)", "Normale (100%)", "Grande (120%)", "Molto Grande (140%)"]
        curr_size = impostazioni.get("font_size", "Normale (100%)")
        nuova_dimensione = st.select_slider(
            "Dimensione testo:", 
            options=size_options, 
            value=curr_size if curr_size in size_options else "Normale (100%)"
        )
        
        density_options = ["Compatta", "Standard", "Spaziosa"]
        curr_dens = impostazioni.get("density", "Standard")
        nuova_densita = st.radio(
            "Densità / Spaziatura:", 
            density_options, 
            index=density_options.index(curr_dens) if curr_dens in density_options else 1, 
            horizontal=True
        )

        alto_contrasto_focus = st.checkbox(
            "Bordo ad alto contrasto per navigazione da tastiera", 
            value=impostazioni.get("high_contrast_focus", True),
            help="Evidenzia con un bordo colorato visibile l'elemento attivo durante l'uso del tasto TAB o ausili motori."
        )

        with st.popover("🛠️ Personalizza Colori Singoli"):
            st.caption("Modifica la palette cromatica nei minimi dettagli:")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                col_bg = st.color_picker("Sfondo Principale", impostazioni.get("bg_color", "#0d1117"))
                col_side = st.color_picker("Sfondo Barra Laterale", impostazioni.get("sidebar_bg_color", "#090d13"))
                col_text = st.color_picker("Colore Testo", impostazioni.get("text_color", "#f0f6fc"))
            with c_p2:
                col_sec = st.color_picker("Sfondo Card / Schede", impostazioni.get("secondary_bg_color", "#161b22"))
                col_acc = st.color_picker("Accento / Pulsanti", impostazioni.get("accent_color", "#ff4b4b"))
                col_border = st.color_picker("Colore Bordi", impostazioni.get("border_color", "#30363d"))

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("💾 Salva Stile", use_container_width=True, type="primary"):
                nuovo_preset = selected_preset
                if (col_bg != impostazioni.get("bg_color") or 
                    col_sec != impostazioni.get("secondary_bg_color") or 
                    col_text != impostazioni.get("text_color") or 
                    col_acc != impostazioni.get("accent_color") or
                    col_side != impostazioni.get("sidebar_bg_color") or
                    col_border != impostazioni.get("border_color")):
                    nuovo_preset = "Personalizzato 🛠️"

                nuova_config = {
                    "preset": nuovo_preset,
                    "bg_color": col_bg,
                    "secondary_bg_color": col_sec,
                    "sidebar_bg_color": col_side,
                    "text_color": col_text,
                    "accent_color": col_acc,
                    "border_color": col_border,
                    "font_family": nuovo_font,
                    "font_size": nuova_dimensione,
                    "density": nuova_densita,
                    "high_contrast_focus": alto_contrasto_focus
                }
                settings_manager.salva_impostazioni(nuova_config)
                st.success("Impostazioni salvate!")
                st.rerun()

        with btn_col2:
            if st.button("🔄 Reset Predefiniti", use_container_width=True):
                settings_manager.salva_impostazioni(settings_manager.DEFAULT_SETTINGS)
                st.rerun()

    # Statistiche rapide
    st.markdown("---")
    totale_memo = len(df)
    urgenti_p1 = len(df[df['priorita'] == 1]) if not df.empty else 0
    scadenze_tot = len(df[df['data_promemoria'].notna() & (df['data_promemoria'] != "")]) if not df.empty else 0
    st.caption(f"📊 Totale: **{totale_memo}** | 🔴 P1: **{urgenti_p1}** | 📅 Scadenze: **{scadenze_tot}**")

# -------------------------------------------------------------
# GESTIONE CONTENUTO PRINCIPALE
# -------------------------------------------------------------
if df.empty:
    st.info("👋 **Benvenuto in Astro_KW MemoBot!** Nessun memo presente nel database. Invia un messaggio o nota vocale al tuo bot su Telegram e premi 'Sincronizza ora' nella barra laterale sinistra.")
    st.markdown("---")
    guida_utente.render_scheda_guida()
else:
    # Applicazione filtri
    df_filtrato = df.copy()

    if search_query:
        df_filtrato = df_filtrato[
            df_filtrato['titolo'].str.contains(search_query, case=False, na=False) |
            df_filtrato['riassunto'].str.contains(search_query, case=False, na=False) |
            df_filtrato['testo_originale'].str.contains(search_query, case=False, na=False) |
            df_filtrato['tags'].str.contains(search_query, case=False, na=False)
        ]

    if priorita_val is not None:
        df_filtrato = df_filtrato[df_filtrato['priorita'] == priorita_val]

    if tipo_selezionato != "Tutti i tipi":
        df_filtrato = df_filtrato[df_filtrato['tipo_contenuto'] == tipo_selezionato]

    if tag_selezionato != "Tutti i tag":
        df_filtrato = df_filtrato[df_filtrato['tags'].str.contains(tag_selezionato, case=False, na=False)]

    # Ordinamento
    if ordinamento == "🕒 Data (Più recenti)":
        df_filtrato = df_filtrato.sort_values(by="data_creazione", ascending=False)
    elif ordinamento == "⚠️ Priorità (P1 in cima)":
        df_filtrato = df_filtrato.sort_values(by=["priorita", "data_creazione"], ascending=[True, False])
    elif ordinamento == "🔤 Titolo (A-Z)":
        df_filtrato = df_filtrato.sort_values(by="titolo", ascending=True)

    # -------------------------------------------------------------
    # SCHEDE TABS: AGENDA + MACRO-AREE
    # -------------------------------------------------------------
    df_agenda = df_filtrato[df_filtrato['data_promemoria'].notna() & (df_filtrato['data_promemoria'] != "")]
    count_agenda = len(df_agenda)

    categorie_tab = [
        ("Tutti", "📋 Tutti"),
        ("Agenda", f"📅 Agenda & Scadenze ({count_agenda})"),
        ("Lavoro", "💼 Lavoro"),
        ("Sport", "⚽ Sport"),
        ("Tempo Libero", "🏖️ Tempo Libero"),
        ("Famiglia/Personale", "🏠 Famiglia"),
        ("Tecnologia", "💻 Tecnologia"),
        ("Cultura/Notizie", "📰 Notizie"),
        ("Spesa/Acquisti", "🛒 Spesa"),
        ("Altro", "📁 Altro"),
        ("Guida", "📖 Guida Utente")
    ]
    
    nomi_tab = []
    for cat_id, cat_label in categorie_tab:
        if cat_id == "Tutti":
            count = len(df_filtrato)
            nomi_tab.append(f"{cat_label} ({count})")
        elif cat_id in ["Agenda", "Guida"]:
            nomi_tab.append(cat_label)
        else:
            count = len(df_filtrato[df_filtrato['categoria'] == cat_id])
            nomi_tab.append(f"{cat_label} ({count})")

    tabs = st.tabs(nomi_tab)

    for i, (cat_id, cat_label) in enumerate(categorie_tab):
        with tabs[i]:
            if cat_id == "Guida":
                guida_utente.render_scheda_guida()
                continue

            if cat_id == "Tutti":
                df_sezione = df_filtrato
            elif cat_id == "Agenda":
                # Vista speciale Agenda ordinata per data scadenza
                df_sezione = df_agenda.sort_values(by="data_promemoria", ascending=True)
            else:
                df_sezione = df_filtrato[df_filtrato['categoria'] == cat_id]

            if df_sezione.empty:
                st.info(f"Nessun elemento presente nella sezione **{cat_label}** con i filtri attuali.")
            else:
                if cat_id == "Agenda" and calendar_sync.is_configured():
                    da_sincronizzare = df_sezione[df_sezione['google_event_id'].isna() | (df_sezione['google_event_id'] == '')]
                    n_da_sinc = len(da_sincronizzare)
                    if n_da_sinc > 0:
                        c_sync_all1, c_sync_all2 = st.columns([3, 1.8], vertical_alignment="center")
                        with c_sync_all1:
                            st.info(f"📅 Hai **{n_da_sinc}** scadenze pronte per il calendario **`FabMemoBot`**.")
                        with c_sync_all2:
                            if st.button(f"🚀 Sincronizza tutte ({n_da_sinc}) su FabMemoBot", type="primary", key="btn_sync_all_gcal", use_container_width=True):
                                with st.spinner("Sincronizzazione scadenze con Google Calendar in corso..."):
                                    tot_ok = 0
                                    for _, r_s in da_sincronizzare.iterrows():
                                        res_s = calendar_sync.inserisci_evento_fabmemobot(
                                            titolo=str(r_s['titolo']),
                                            data_promemoria_str=str(r_s['data_promemoria']),
                                            riassunto=str(r_s['riassunto']),
                                            link_originale=str(r_s['link_originale'])
                                        )
                                        if res_s.get("success"):
                                            database.segna_sincronizzato_gcal(int(r_s['id']), res_s.get("event_id"))
                                            tot_ok += 1
                                    st.success(f"{tot_ok} scadenze sincronizzate direttamente in FabMemoBot!")
                                    st.rerun()
                # Calcolo elementi selezionati per la scheda corrente
                ids_sezione = [int(m_id) for m_id in df_sezione['id']]
                selezionati = [m_id for m_id in ids_sezione if st.session_state.get(f"sel_{cat_id}_{m_id}", False)]
                n_sel = len(selezionati)

                # Toolbar di Selezione e Azioni di Gruppo
                col_info, col_sel_all, col_sel_none, col_bulk_del = st.columns([3, 1.2, 1.2, 2.2], vertical_alignment="center")
                
                with col_info:
                    st.write(f"Mostrati **{len(df_sezione)}** memo | **{n_sel}** selezionati")
                    
                with col_sel_all:
                    if st.button("☑️ Tutti", key=f"btn_all_{cat_id}", help="Seleziona tutti i memo di questa scheda", use_container_width=True):
                        for m_id in ids_sezione:
                            st.session_state[f"sel_{cat_id}_{m_id}"] = True
                        st.rerun()

                with col_sel_none:
                    if st.button("⬜ Nessuno", key=f"btn_none_{cat_id}", help="Deseleziona tutti i memo", use_container_width=True):
                        for m_id in ids_sezione:
                            st.session_state[f"sel_{cat_id}_{m_id}"] = False
                        st.rerun()

                with col_bulk_del:
                    if n_sel > 0:
                        with st.popover(f"🗑️ Elimina ({n_sel})", use_container_width=True):
                            st.markdown(f"⚠️ **Eliminazione Multipla**")
                            st.write(f"Vuoi eliminare definitivamente i **{n_sel}** memo selezionati?")
                            if st.button(f"🔥 Sì, Elimina {n_sel} memo", type="primary", key=f"confirm_bulk_{cat_id}", use_container_width=True):
                                cancellati = database.elimina_memo_multipli(selezionati)
                                for m_id in selezionati:
                                    st.session_state.pop(f"sel_{cat_id}_{m_id}", None)
                                st.success(f"{cancellati} memo eliminati con successo!")
                                st.rerun()
                    else:
                        st.button("🗑️ Elimina selezionati", disabled=True, key=f"btn_bulk_del_dis_{cat_id}", use_container_width=True)

                st.write("")

                for _, row in df_sezione.iterrows():
                    memo_id = int(row['id'])
                    p_val = int(row['priorita'])
                    
                    if p_val == 1:
                        badge_p = "🔴 [P1 - URGENTE]"
                    elif p_val == 2:
                        badge_p = "🟡 [P2 - MEDIA]"
                    else:
                        badge_p = "🟢 [P3]"

                    tipo_str = str(row['tipo_contenuto']).upper()
                    cat_str = str(row['categoria'])
                    titolo_memo = str(row['titolo']) or "Senza Titolo"
                    data_str = str(row['data_creazione'])
                    promemoria_val = str(row['data_promemoria']) if (pd.notna(row['data_promemoria']) and row['data_promemoria']) else ""

                    badge_agenda = f" | 📅 SCADENZA: {promemoria_val}" if promemoria_val else ""
                    header_text = f"{badge_p} 📌 **{titolo_memo}** — *({tipo_str} | {cat_str}){badge_agenda}* - {data_str}"

                    col_chk, col_exp = st.columns([0.05, 0.95], vertical_alignment="top")
                    with col_chk:
                        st.checkbox("", key=f"sel_{cat_id}_{memo_id}", label_visibility="collapsed")
                    with col_exp:
                        with st.expander(header_text):
                            # Visualizzazione Contenuto
                            st.markdown(f"**Riassunto AI:** {row['riassunto']}")
                            
                            if promemoria_val:
                                st.info(f"⏰ **Data Promemoria Rilevata:** `{promemoria_val}`")
                                gcal_synced_id = str(row.get('google_event_id') or '').strip()
                                
                                if gcal_synced_id and gcal_synced_id.lower() not in ['none', 'nan', '']:
                                    st.success("✅ **Sincronizzato sul calendario Google `FabMemoBot`!**")
                                else:
                                    if calendar_sync.is_configured():
                                        col_g1, col_g2 = st.columns([1.2, 1])
                                        with col_g1:
                                            if st.button("🚀 Sincronizza su FabMemoBot (1-Click)", key=f"btn_sync_gcal_{cat_id}_{memo_id}", type="primary"):
                                                with st.spinner("Sincronizzazione in corso con Google Calendar..."):
                                                    res = calendar_sync.inserisci_evento_fabmemobot(
                                                        titolo=titolo_memo,
                                                        data_promemoria_str=promemoria_val,
                                                        riassunto=row['riassunto'],
                                                        link_originale=row['link_originale']
                                                    )
                                                    if res.get("success"):
                                                        database.segna_sincronizzato_gcal(memo_id, res.get("event_id"))
                                                        st.success("Evento inserito direttamente in FabMemoBot!")
                                                        st.rerun()
                                                    else:
                                                        st.error(f"Errore: {res.get('error')}")
                                        with col_g2:
                                            gcal_url = genera_link_google_calendar(
                                                titolo=titolo_memo,
                                                data_promemoria_str=promemoria_val,
                                                testo=row['riassunto'],
                                                link_originale=row['link_originale']
                                            )
                                            if gcal_url:
                                                st.markdown(f'''
                                                    <a href="{gcal_url}" target="_blank" style="text-decoration: none;">
                                                        <button style="background-color: #3c4043; color: white; border: none; padding: 7px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; font-weight: 500;">
                                                            🌐 Apri nel Web
                                                        </button>
                                                    </a>
                                                ''', unsafe_allow_html=True)
                                    else:
                                        gcal_url = genera_link_google_calendar(
                                            titolo=titolo_memo,
                                            data_promemoria_str=promemoria_val,
                                            testo=row['riassunto'],
                                            link_originale=row['link_originale']
                                        )
                                        if gcal_url:
                                            st.markdown(f'''
                                                <a href="{gcal_url}" target="_blank" style="text-decoration: none;">
                                                    <button style="background-color: #1a73e8; color: white; border: none; padding: 6px 14px; border-radius: 4px; cursor: pointer; font-size: 0.9rem; font-weight: 500;">
                                                        📅 Aggiungi a Google Calendar (FabMemoBot)
                                                    </button>
                                                </a>
                                            ''', unsafe_allow_html=True)
                                        st.caption("💡 *Per l'invio diretto in 1-Click senza passare dal browser, posiziona `credentials.json` nella cartella principale di MemoBot.*")
                                st.write("")

                            if row['link_originale']:
                                st.markdown(f"🔗 **Link:** [{row['link_originale']}]({row['link_originale']})")
                                
                            st.markdown("**Testo Originale / Trascrizione / OCR:**")
                            st.text(row['testo_originale'])
                            
                            if row['tags']:
                                tags_list = [f"`{t.strip()}`" for t in str(row['tags']).split(',') if t.strip()]
                                st.markdown("**Tags:** " + " ".join(tags_list))

                            st.markdown("---")
                            
                            # BARRA DELLE AZIONI (CONDIVIDI, MODIFICA ED ELIMINA)
                            col_share, col_azioni, col_elimina = st.columns([1.6, 1.4, 1])

                            with col_share:
                                with st.popover("📲 Condividi / Copia"):
                                    testo_condivisione = f"📌 *{titolo_memo}*\n\n💡 *Riassunto:*\n{row['riassunto']}"
                                    if promemoria_val:
                                        testo_condivisione += f"\n\n⏰ *Scadenza:* {promemoria_val}"
                                    if row['link_originale']:
                                        testo_condivisione += f"\n\n🔗 *Fonte:* {row['link_originale']}"
                                    
                                    st.caption("Copia con l'icona in alto a destra o clicca per inviare:")
                                    st.code(testo_condivisione, language="markdown")
                                    
                                    enc_text = urllib.parse.quote(testo_condivisione)
                                    url_wa = f"https://api.whatsapp.com/send?text={enc_text}"
                                    link_param = urllib.parse.quote(str(row['link_originale'] or ''))
                                    url_tg = f"https://t.me/share/url?url={link_param}&text={enc_text}" if row['link_originale'] else f"https://t.me/share/url?text={enc_text}"
                                    
                                    c_wa, c_tg = st.columns(2)
                                    with c_wa:
                                        st.markdown(f'''
                                            <a href="{url_wa}" target="_blank" style="text-decoration: none;">
                                                <button style="width: 100%; background-color: #25D366; color: white; border: none; padding: 7px 10px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; font-weight: 600;">
                                                    🟢 WhatsApp
                                                </button>
                                            </a>
                                        ''', unsafe_allow_html=True)
                                    with c_tg:
                                        st.markdown(f'''
                                            <a href="{url_tg}" target="_blank" style="text-decoration: none;">
                                                <button style="width: 100%; background-color: #229ED9; color: white; border: none; padding: 7px 10px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; font-weight: 600;">
                                                    🔵 Telegram
                                                </button>
                                            </a>
                                        ''', unsafe_allow_html=True)

                            with col_elimina:
                                with st.popover("🗑️ Elimina"):
                                    st.write(f"Vuoi eliminare definitivamente questo memo #{memo_id}?")
                                    if st.button("Sì, Elimina", key=f"del_{cat_id}_{memo_id}", type="primary"):
                                        if database.elimina_memo(memo_id):
                                            st.session_state.pop(f"sel_{cat_id}_{memo_id}", None)
                                            st.success("Eliminato!")
                                            st.rerun()
                                        else:
                                            st.error("Errore eliminazione.")

                            with col_azioni:
                                with st.popover("✏️ Modifica"):
                                    st.write(f"**Modifica Memo #{memo_id}**")
                                    mod_titolo = st.text_input("Titolo:", value=titolo_memo, key=f"edit_tit_{cat_id}_{memo_id}")
                                    
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        idx_cat = database.CATEGORIE_STANDARD.index(cat_str) if cat_str in database.CATEGORIE_STANDARD else 7
                                        mod_categoria = st.selectbox("Categoria:", database.CATEGORIE_STANDARD, index=idx_cat, key=f"edit_cat_{cat_id}_{memo_id}")
                                    with c2:
                                        mod_priorita = st.selectbox("Priorità:", [1, 2, 3], index=[1, 2, 3].index(p_val if p_val in [1, 2, 3] else 3), key=f"edit_pri_{cat_id}_{memo_id}", format_func=lambda x: {1: "🔴 P1 - Alta/Urgente", 2: "🟡 P2 - Media", 3: "🟢 P3 - Normale"}[x])
                                    
                                    mod_promemoria = st.text_input("Data/Ora Promemoria (es: 2026-10-15 20:00 o vuoto):", value=promemoria_val, key=f"edit_pro_{cat_id}_{memo_id}")
                                    mod_riassunto = st.text_area("Riassunto AI:", value=str(row['riassunto']), key=f"edit_ria_{cat_id}_{memo_id}")
                                    mod_tags = st.text_input("Tags (separati da virgola):", value=str(row['tags']), key=f"edit_tag_{cat_id}_{memo_id}")
                                    mod_testo = st.text_area("Testo originale / trascrizione:", value=str(row['testo_originale']), key=f"edit_txt_{cat_id}_{memo_id}")

                                    if st.button("💾 Salva Modifiche", key=f"btn_save_{cat_id}_{memo_id}"):
                                        conn_m = database.get_connection()
                                        cur_m = conn_m.cursor()
                                        # Se la data è stata modificata, azzera google_event_id per consentire una nuova sincronizzazione
                                        nuovo_gcal_id = row.get('google_event_id') if mod_promemoria == promemoria_val else None
                                        cur_m.execute('''
                                            UPDATE memo
                                            SET titolo = ?, riassunto = ?, testo_originale = ?, categoria = ?, priorita = ?, tags = ?, data_promemoria = ?, google_event_id = ?
                                            WHERE id = ?
                                        ''', (mod_titolo, mod_riassunto, mod_testo, mod_categoria, mod_priorita, mod_tags, mod_promemoria if mod_promemoria else None, nuovo_gcal_id, memo_id))
                                        conn_m.commit()
                                        conn_m.close()
                                        st.success("Modifiche salvate con successo!")
                                        st.rerun()