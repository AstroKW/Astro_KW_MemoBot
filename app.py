import os
import sys
import subprocess
import urllib.parse
import re
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import database
import calendar_sync
import settings_manager
import guida_utente
import radar_processor
import podcast_feed

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

# Inizializza o migra il DB all'avvio (eseguito solo una volta per sessione per massima reattività)
if "db_initialized" not in st.session_state:
    database.init_db()
    st.session_state["db_initialized"] = True

# Avvio in background del server HTTP locale per il Feed RSS di AntennaPod (porta 8503)
podcast_feed.avvia_server_podcast_background()

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

        if 'archiviato' not in df.columns:
            df['archiviato'] = 0
        else:
            df['archiviato'] = df['archiviato'].fillna(0).astype(int)

        if 'cestinato' not in df.columns:
            df['cestinato'] = 0
        else:
            df['cestinato'] = df['cestinato'].fillna(0).astype(int)

        if 'audio_podcast_path' not in df.columns:
            df['audio_podcast_path'] = None

        if 'podcast_incluso' not in df.columns:
            df['podcast_incluso'] = 0
        else:
            df['podcast_incluso'] = df['podcast_incluso'].fillna(0).astype(int)

        if 'podcast_durata' not in df.columns:
            df['podcast_durata'] = 0
        else:
            df['podcast_durata'] = df['podcast_durata'].fillna(0).astype(int)

        if 'podcast_intro' not in df.columns:
            df['podcast_intro'] = None
            
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

    # 6. Ordinamento & Vista
    st.markdown("---")
    st.subheader("⚙️ Ordinamento & Vista")
    ordinamento = st.radio(
        "Ordina memo per:",
        ["🕒 Data (Più recenti)", "⚠️ Priorità (P1 in cima)", "🔤 Titolo (A-Z)"]
    )
    
    opzioni_limite = ["25 memo", "50 memo", "Tutti"]
    limite_default = st.session_state.get("cfg_memo_limit", "25 memo")
    if limite_default not in opzioni_limite:
        limite_default = "25 memo"
    limite_scelto = st.selectbox(
        "Mostra per pagina:",
        options=opzioni_limite,
        index=opzioni_limite.index(limite_default),
        key="cfg_memo_limit",
        help="Visualizzare 25 o 50 memo velocizza enormemente l'interfaccia rendendo i clic istantanei."
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

    # MOTORE INTELLIGENZA ARTIFICIALE (LOCALE / CLOUD)
    st.markdown("---")
    with st.expander("🤖 Motore AI (Locale & Cloud)", expanded=False):
        import ai_service
        active_provider = ai_service.get_provider()
        st.markdown(f"**Attivo:** `{ai_service.get_active_provider_label()}`")
        
        if st.button("🧪 Testa Connessione AI", key="btn_test_ai_sidebar", use_container_width=True):
            with st.spinner("Test in corso..."):
                ok, msg, elapsed = ai_service.test_connessione_ai()
                if ok:
                    st.success(f"✅ Riuscito in {elapsed}s!")
                else:
                    st.error(f"❌ {msg}")
        
        st.markdown("---")
        st.caption("Configura fornitore e modelli:")
        
        provider_options = {
            "ollama": "🏠 Ollama (Locale - Privacy 100%)",
            "gemini": "☁️ Google Gemini (Cloud Gratuito / Pro)",
            "groq": "⚡ Groq (Cloud Ultra-Veloce)",
            "openai": "💳 OpenAI ChatGPT (Cloud)",
            "openrouter": "🌐 OpenRouter (Tutti i Modelli)",
            "custom": "🛠️ Endpoint Personalizzato"
        }
        
        idx_prov = list(provider_options.keys()).index(active_provider) if active_provider in provider_options else 0
        sel_prov = st.selectbox(
            "Fornitore AI:",
            options=list(provider_options.keys()),
            format_func=lambda x: provider_options[x],
            index=idx_prov,
            key="ai_provider_select_sb"
        )
        
        aggiornamenti_env = {"AI_PROVIDER": sel_prov}
        
        if sel_prov == "ollama":
            curr_ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
            nuovo_ollama_model = st.text_input("Modello Testo:", value=curr_ollama_model, key="cfg_ollama_model")
            curr_ollama_vision = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:7b")
            nuovo_ollama_vision = st.text_input("Modello Vision:", value=curr_ollama_vision, key="cfg_ollama_vision")
            aggiornamenti_env["OLLAMA_MODEL"] = nuovo_ollama_model
            aggiornamenti_env["OLLAMA_VISION_MODEL"] = nuovo_ollama_vision
            st.caption("💡 *Richiede Ollama attivo sul PC.*")
            
        elif sel_prov == "gemini":
            curr_gemini_key = os.getenv("GEMINI_API_KEY", "")
            nuova_gemini_key = st.text_input("Gemini API Key:", value=curr_gemini_key, type="password", key="cfg_gemini_key")
            curr_gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            nuovo_gemini_model = st.text_input("Modello Gemini:", value=curr_gemini_model, key="cfg_gemini_model")
            aggiornamenti_env["GEMINI_API_KEY"] = nuova_gemini_key
            aggiornamenti_env["GEMINI_MODEL"] = nuovo_gemini_model
            st.caption("💡 *Ottieni la chiave gratuita su [Google AI Studio](https://aistudio.google.com/).*")
            
        elif sel_prov == "groq":
            curr_groq_key = os.getenv("GROQ_API_KEY", "")
            nuova_groq_key = st.text_input("Groq API Key:", value=curr_groq_key, type="password", key="cfg_groq_key")
            curr_groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            nuovo_groq_model = st.text_input("Modello Groq:", value=curr_groq_model, key="cfg_groq_model")
            aggiornamenti_env["GROQ_API_KEY"] = nuova_groq_key
            aggiornamenti_env["GROQ_MODEL"] = nuovo_groq_model
            st.caption("💡 *Ottieni la chiave su [console.groq.com](https://console.groq.com/).*")
            
        elif sel_prov == "openai":
            curr_openai_key = os.getenv("OPENAI_API_KEY", "")
            nuova_openai_key = st.text_input("OpenAI API Key:", value=curr_openai_key, type="password", key="cfg_openai_key")
            curr_openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            nuovo_openai_model = st.text_input("Modello OpenAI:", value=curr_openai_model, key="cfg_openai_model")
            aggiornamenti_env["OPENAI_API_KEY"] = nuova_openai_key
            aggiornamenti_env["OPENAI_MODEL"] = nuovo_openai_model
            
        elif sel_prov == "openrouter":
            curr_openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
            nuova_openrouter_key = st.text_input("OpenRouter API Key:", value=curr_openrouter_key, type="password", key="cfg_openrouter_key")
            curr_openrouter_model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
            nuovo_openrouter_model = st.text_input("Modello OpenRouter:", value=curr_openrouter_model, key="cfg_openrouter_model")
            aggiornamenti_env["OPENROUTER_API_KEY"] = nuova_openrouter_key
            aggiornamenti_env["OPENROUTER_MODEL"] = nuovo_openrouter_model
            
        elif sel_prov == "custom":
            curr_custom_url = os.getenv("CUSTOM_OPENAI_BASE_URL", "")
            nuovo_custom_url = st.text_input("Base URL:", value=curr_custom_url, key="cfg_custom_url")
            curr_custom_key = os.getenv("CUSTOM_OPENAI_API_KEY", "")
            nuova_custom_key = st.text_input("API Key:", value=curr_custom_key, type="password", key="cfg_custom_key")
            curr_custom_model = os.getenv("CUSTOM_OPENAI_MODEL", "")
            nuovo_custom_model = st.text_input("Modello:", value=curr_custom_model, key="cfg_custom_model")
            aggiornamenti_env["CUSTOM_OPENAI_BASE_URL"] = nuovo_custom_url
            aggiornamenti_env["CUSTOM_OPENAI_API_KEY"] = nuova_custom_key
            aggiornamenti_env["CUSTOM_OPENAI_MODEL"] = nuovo_custom_model
            
        if st.button("💾 Salva Configurazione AI", key="btn_save_ai_cfg", type="primary", use_container_width=True):
            if ai_service.salva_configurazione_env(aggiornamenti_env):
                st.success("Configurazione salvata con successo!")
                st.rerun()
            else:
                st.error("Errore nel salvataggio della configurazione.")

    # PODCAST & AUDIOBOOKS (ANTENNAPOD / ANDROID AUTO)
    st.markdown("---")
    with st.expander("🎙️ Podcast & Audio (AntennaPod)", expanded=False):
        st.caption("Configura voce e sintesi per l'ascolto su Android Auto:")
        auto_gen = st.checkbox(
            "Genera automaticamente podcast da articoli web inviati via Telegram",
            value=bool(impostazioni.get("podcast_auto_generate", True)),
            key="cfg_podcast_auto"
        )
        
        import podcast_tts
        voci_disponibili = podcast_tts.elenca_voci_disponibili()
        curr_voce = impostazioni.get("podcast_voice", "im_nicola")
        if curr_voce not in voci_disponibili:
            curr_voce = "im_nicola"
            
        voce_selezionata = st.selectbox(
            "Voce narratore:",
            options=list(voci_disponibili.keys()),
            format_func=lambda x: voci_disponibili[x],
            index=list(voci_disponibili.keys()).index(curr_voce),
            key="cfg_podcast_voice"
        )

        with st.popover("➕ Carica Nuova Voce Campione"):
            st.caption("Carica un audio di 10–25s (senza musica) per clonare una nuova voce con la GPU:")
            uploaded_v = st.file_uploader("File audio (.wav / .mp3):", type=["wav", "mp3", "ogg", "flac"], key="upl_voice_sb")
            nome_v = st.text_input("Nome della voce (es. Alberto Angela):", key="txt_voice_name_sb")
            if st.button("Salva Campione Voce", key="btn_save_voice_sb", type="primary", use_container_width=True):
                if uploaded_v and nome_v.strip():
                    import re
                    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', nome_v.strip().lower())
                    ext = os.path.splitext(uploaded_v.name)[1].lower()
                    target_p = os.path.join(podcast_tts.VOCI_DIR, f"{clean_name}{ext}")
                    with open(target_p, "wb") as f_v:
                        f_v.write(uploaded_v.read())
                    st.success(f"Voce '{nome_v.strip()}' aggiunta!")
                    st.rerun()
                else:
                    st.warning("Seleziona un file audio e indica il nome.")
        
        curr_speed = float(impostazioni.get("podcast_speed", 1.0))
        speed_sel = st.slider(
            "Velocità di lettura:",
            min_value=0.8,
            max_value=1.3,
            value=curr_speed,
            step=0.05,
            key="cfg_podcast_speed"
        )
        
        if st.button("💾 Salva Impostazioni Podcast", key="btn_save_podcast_cfg", type="primary", use_container_width=True):
            nuove_imp = impostazioni.copy()
            nuove_imp["podcast_auto_generate"] = auto_gen
            nuove_imp["podcast_voice"] = voce_selezionata
            nuove_imp["podcast_speed"] = speed_sel
            if voce_selezionata.startswith("clone:"):
                nuove_imp["podcast_engine"] = "xtts"
            elif "Neural" in voce_selezionata:
                nuove_imp["podcast_engine"] = "edge"
            else:
                nuove_imp["podcast_engine"] = "kokoro"
            settings_manager.salva_impostazioni(nuove_imp)
            st.success("Impostazioni podcast aggiornate!")
            st.rerun()

    # Statistiche rapide
    st.markdown("---")
    totale_memo = len(df)
    non_cestinati = df[df['cestinato'] == 0] if not df.empty else df
    attivi_tot = len(non_cestinati[non_cestinati['archiviato'] == 0]) if not df.empty else 0
    archiviati_tot = len(non_cestinati[non_cestinati['archiviato'] == 1]) if not df.empty else 0
    cestinati_tot = len(df[df['cestinato'] == 1]) if not df.empty else 0
    urgenti_p1 = len(non_cestinati[(non_cestinati['priorita'] == 1) & (non_cestinati['archiviato'] == 0)]) if not df.empty else 0
    scadenze_tot = len(non_cestinati[non_cestinati['data_promemoria'].notna() & (non_cestinati['data_promemoria'] != "") & (non_cestinati['archiviato'] == 0)]) if not df.empty else 0
    st.caption(f"📊 Attivi: **{attivi_tot}** | 🔴 P1: **{urgenti_p1}** | 📅 Scadenze: **{scadenze_tot}** | 📦 Archiviati: **{archiviati_tot}** | 🗑️ Cestino: **{cestinati_tot}**")

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
    # FINESTRA MODALE MODIFICA MEMO (@st.dialog ON-DEMAND)
    # -------------------------------------------------------------
    @st.dialog("✏️ Modifica Memo", width="large")
    def dialog_modifica_memo(memo_dict):
        memo_id = int(memo_dict['id'])
        titolo_memo = str(memo_dict.get('titolo') or '')
        cat_str = str(memo_dict.get('categoria') or 'Altro')
        p_val = int(memo_dict.get('priorita') or 3)
        promemoria_val = str(memo_dict.get('data_promemoria') or '')
        if promemoria_val in ['None', 'nan']:
            promemoria_val = ''
        is_archived = bool(int(memo_dict.get('archiviato') or 0))
        allegato_file = str(memo_dict.get('allegato_path') or '').strip()

        st.markdown(f"#### Modifica Memo **#{memo_id}**")
        mod_titolo = st.text_input("Titolo:", value=titolo_memo, key=f"dlg_tit_{memo_id}")

        c1, c2 = st.columns(2)
        with c1:
            idx_cat = database.CATEGORIE_STANDARD.index(cat_str) if cat_str in database.CATEGORIE_STANDARD else 7
            mod_categoria = st.selectbox("Categoria:", database.CATEGORIE_STANDARD, index=idx_cat, key=f"dlg_cat_{memo_id}")
        with c2:
            mod_priorita = st.selectbox(
                "Priorità:",
                [1, 2, 3],
                index=[1, 2, 3].index(p_val if p_val in [1, 2, 3] else 3),
                key=f"dlg_pri_{memo_id}",
                format_func=lambda x: {1: "🔴 P1 - Alta/Urgente", 2: "🟡 P2 - Media", 3: "🟢 P3 - Normale"}.get(x, str(x))
            )

        mod_promemoria = st.text_input("Data/Ora Promemoria (es: 2026-10-15 20:00 o vuoto):", value=promemoria_val, key=f"dlg_pro_{memo_id}")
        mod_archiviato = st.checkbox("Sposta in Archivio (Completato)", value=is_archived, key=f"dlg_arch_{memo_id}")
        mod_riassunto = st.text_area("Riassunto AI:", value=str(memo_dict.get('riassunto') or ''), height=100, key=f"dlg_ria_{memo_id}")
        mod_tags = st.text_input("Tags (separati da virgola):", value=str(memo_dict.get('tags') or ''), key=f"dlg_tag_{memo_id}")
        mod_testo = st.text_area("Testo originale / trascrizione:", value=str(memo_dict.get('testo_originale') or ''), height=140, key=f"dlg_txt_{memo_id}")

        st.markdown("---")
        st.markdown("**📷 Allegato Immagine:**")
        ha_allegato = bool(allegato_file and allegato_file.lower() not in ['none', 'nan', ''] and os.path.exists(allegato_file))
        if ha_allegato:
            st.caption(f"File presente: `{os.path.basename(allegato_file)}`")
            rimuovi_allegato_chk = st.checkbox("🗑️ Rimuovi immagine allegata", key=f"dlg_rm_{memo_id}")
        else:
            rimuovi_allegato_chk = False

        nuovo_file_up = st.file_uploader("Allega o sostituisci foto (JPG, PNG):", type=["jpg", "jpeg", "png", "webp"], key=f"dlg_up_{memo_id}")

        c_b1, c_b2 = st.columns([1, 1])
        with c_b1:
            if st.button("💾 Salva Modifiche", type="primary", use_container_width=True, key=f"dlg_save_{memo_id}"):
                conn_m = database.get_connection()
                cur_m = conn_m.cursor()
                nuovo_gcal_id = memo_dict.get('google_event_id') if mod_promemoria == promemoria_val else None
                cur_m.execute('''
                    UPDATE memo
                    SET titolo = ?, riassunto = ?, testo_originale = ?, categoria = ?, priorita = ?, tags = ?, data_promemoria = ?, google_event_id = ?, archiviato = ?
                    WHERE id = ?
                ''', (mod_titolo, mod_riassunto, mod_testo, mod_categoria, mod_priorita, mod_tags, mod_promemoria if mod_promemoria else None, nuovo_gcal_id, 1 if mod_archiviato else 0, memo_id))
                conn_m.commit()
                conn_m.close()

                if rimuovi_allegato_chk:
                    database.rimuovi_allegato(memo_id)
                elif nuovo_file_up is not None:
                    os.makedirs("allegati", exist_ok=True)
                    os.makedirs("downloads", exist_ok=True)
                    dest_path = os.path.join("allegati", f"foto_manuale_{memo_id}.jpg")
                    temp_path = os.path.join("downloads", f"temp_up_{memo_id}.jpg")
                    with open(temp_path, "wb") as f_up:
                        f_up.write(nuovo_file_up.getbuffer())
                    from telegram_sync import ottimizza_e_salva_immagine
                    ottimizza_e_salva_immagine(temp_path, dest_path)
                    if os.path.exists(temp_path):
                        try: os.remove(temp_path)
                        except: pass
                    database.imposta_allegato(memo_id, dest_path)

                st.success("Modifiche salvate con successo!")
                st.rerun()

    # -------------------------------------------------------------
    # SCHEDE TABS: AGENDA + MACRO-AREE + ARCHIVIO + CESTINO
    # -------------------------------------------------------------
    df_non_cestinati = df_filtrato[df_filtrato['cestinato'] == 0]
    df_attivi = df_non_cestinati[df_non_cestinati['archiviato'] == 0]
    df_archiviati = df_non_cestinati[df_non_cestinati['archiviato'] == 1]
    df_cestinati = df_filtrato[df_filtrato['cestinato'] == 1]

    df_agenda = df_attivi[df_attivi['data_promemoria'].notna() & (df_attivi['data_promemoria'] != "")]
    df_podcast = df_non_cestinati[df_non_cestinati['audio_podcast_path'].notna() & (df_non_cestinati['audio_podcast_path'] != '')] if 'audio_podcast_path' in df_non_cestinati.columns else pd.DataFrame()
    count_agenda = len(df_agenda)
    count_podcast = len(df_podcast)
    count_archiviati = len(df_archiviati)
    count_cestinati = len(df_cestinati)

    categorie_tab = [
        ("Tutti", "📋 Tutti"),
        ("Podcast", f"🎙️ Podcast & Audio ({count_podcast})"),
        ("Agenda", f"📅 Agenda & Scadenze ({count_agenda})"),
        ("Radar", "🔭 Astro_KW Radar"),
        ("Lavoro", "💼 Lavoro"),
        ("Sport", "⚽ Sport"),
        ("Tempo Libero", "🏖️ Tempo Libero"),
        ("Famiglia/Personale", "🏠 Famiglia"),
        ("Tecnologia", "💻 Tecnologia"),
        ("Cultura/Notizie", "📰 Notizie"),
        ("Spesa/Acquisti", "🛒 Spesa"),
        ("Altro", "📁 Altro"),
        ("Archivio", f"📦 Archivio ({count_archiviati})"),
        ("Cestino", f"🗑️ Cestino ({count_cestinati})"),
        ("Guida", "📖 Guida Utente")
    ]
    
    mappa_nomi = {}
    for cid, clbl in categorie_tab:
        if cid == "Tutti":
            count = len(df_attivi)
            mappa_nomi[cid] = f"{clbl} ({count})"
        elif cid in ["Agenda", "Guida", "Radar", "Podcast", "Archivio", "Cestino"]:
            mappa_nomi[cid] = clbl
        else:
            count = len(df_attivi[df_attivi['categoria'] == cid])
            mappa_nomi[cid] = f"{clbl} ({count})"

    cat_keys = [c[0] for c in categorie_tab]
    current_tab = st.session_state.get("nav_active_section", "Tutti")
    if current_tab not in cat_keys:
        current_tab = "Tutti"

    active_cat = st.pills(
        "Sezione",
        options=cat_keys,
        default=current_tab,
        format_func=lambda cid: mappa_nomi.get(cid, cid),
        key="nav_active_section",
        label_visibility="collapsed"
    )
    if not active_cat:
        active_cat = current_tab

    cat_id = active_cat
    cat_label = mappa_nomi.get(cat_id, cat_id)

    # Banner globale non bloccante per sintesi podcast in corso / completate in background
    podcast_feed.render_banner_job_podcast()

    st.markdown("")

    if cat_id == "Guida":
        guida_utente.render_scheda_guida()
    elif cat_id == "Radar":
        radar_processor.render_scheda_radar(df[df['cestinato'] == 0])
    elif cat_id == "Podcast":
        podcast_feed.render_scheda_podcast(df_non_cestinati)
    else:
        if cat_id == "Cestino":
            df_sezione = df_cestinati
        elif cat_id == "Archivio":
            df_sezione = df_archiviati
        elif cat_id == "Tutti":
            df_sezione = df_attivi
        elif cat_id == "Agenda":
            df_sezione = df_agenda.sort_values(by="data_promemoria", ascending=True)
        else:
            df_sezione = df_attivi[df_attivi['categoria'] == cat_id]

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
            # Calcolo elementi e limite di visualizzazione (paginazione rapida)
            limite_cfg = st.session_state.get("cfg_memo_limit", "25 memo")
            if limite_cfg == "25 memo":
                limite_n = 25
            elif limite_cfg == "50 memo":
                limite_n = 50
            else:
                limite_n = len(df_sezione)

            df_mostrati = df_sezione.head(limite_n)
            ids_mostrati = [int(m_id) for m_id in df_mostrati['id']]
            ids_sezione = ids_mostrati  # Per selezione coerente con quanto mostrato
            selezionati = [m_id for m_id in ids_mostrati if st.session_state.get(f"sel_{cat_id}_{m_id}", False)]
            n_sel = len(selezionati)

            # Toolbar di Selezione e Azioni di Gruppo
            col_info, col_sel_all, col_sel_none, col_bulk_cat, col_bulk_prio, col_bulk_action, col_bulk_del = st.columns(
                [2.2, 0.9, 0.9, 1.4, 1.4, 1.4, 1.4], vertical_alignment="center"
            )
            
            with col_info:
                if len(df_sezione) > len(df_mostrati):
                    st.write(f"Mostrati **{len(df_mostrati)} su {len(df_sezione)}** | **{n_sel}** sel.")
                else:
                    st.write(f"Mostrati **{len(df_sezione)}** memo | **{n_sel}** sel.")
                
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

            with col_bulk_cat:
                if cat_id != "Cestino" and n_sel > 0:
                    with st.popover(f"🏷️ Categoria ({n_sel})", use_container_width=True):
                        st.markdown("🏷️ **Cambio Categoria di Gruppo**")
                        st.write(f"Assegna una nuova categoria ai **{n_sel}** memo selezionati:")
                        nuova_cat = st.selectbox(
                            "Scegli Categoria:",
                            database.CATEGORIE_STANDARD,
                            key=f"sel_bulk_cat_{cat_id}"
                        )
                        if st.button(f"Assegna '{nuova_cat}' a {n_sel} memo", type="primary", key=f"btn_confirm_bulk_cat_{cat_id}", use_container_width=True):
                            modificati = database.cambia_categoria_multipli(selezionati, nuova_cat)
                            for m_id in selezionati:
                                st.session_state.pop(f"sel_{cat_id}_{m_id}", None)
                            st.success(f"✅ Assegnata categoria '{nuova_cat}' a {modificati} memo!")
                            st.rerun()
                else:
                    st.button("🏷️ Categoria", disabled=True, key=f"btn_bulk_cat_dis_{cat_id}", use_container_width=True)

            with col_bulk_prio:
                if cat_id != "Cestino" and n_sel > 0:
                    with st.popover(f"🎯 Priorità ({n_sel})", use_container_width=True):
                        st.markdown("🎯 **Cambio Priorità di Gruppo**")
                        st.write(f"Assegna una nuova priorità ai **{n_sel}** memo selezionati:")
                        prio_map = {
                            1: "🔴 P1 - Alta / Urgente",
                            2: "🟡 P2 - Media",
                            3: "🟢 P3 - Normale"
                        }
                        nuova_prio = st.selectbox(
                            "Scegli Priorità:",
                            [1, 2, 3],
                            format_func=lambda x: prio_map.get(x, str(x)),
                            key=f"sel_bulk_prio_{cat_id}"
                        )
                        if st.button(f"Assegna {prio_map[nuova_prio]} a {n_sel} memo", type="primary", key=f"btn_confirm_bulk_prio_{cat_id}", use_container_width=True):
                            modificati = database.cambia_priorita_multipli(selezionati, nuova_prio)
                            for m_id in selezionati:
                                st.session_state.pop(f"sel_{cat_id}_{m_id}", None)
                            st.success(f"✅ Assegnata priorità {prio_map[nuova_prio]} a {modificati} memo!")
                            st.rerun()
                else:
                    st.button("🎯 Priorità", disabled=True, key=f"btn_bulk_prio_dis_{cat_id}", use_container_width=True)

            with col_bulk_action:
                if cat_id == "Cestino":
                    if n_sel > 0:
                        if st.button(f"↩️ Ripristina ({n_sel})", key=f"btn_bulk_restore_trash_{cat_id}", help="Ripristina i memo selezionati dal cestino", use_container_width=True):
                            ripristinati = database.ripristina_dal_cestino_multipli(selezionati)
                            for m_id in selezionati:
                                st.session_state.pop(f"sel_{cat_id}_{m_id}", None)
                            st.success(f"{ripristinati} memo ripristinati dal Cestino!")
                            st.rerun()
                    else:
                        st.button("↩️ Ripristina", disabled=True, key=f"btn_bulk_restore_trash_dis_{cat_id}", use_container_width=True)
                elif cat_id == "Archivio":
                    if n_sel > 0:
                        if st.button(f"↩️ Ripristina ({n_sel})", key=f"btn_bulk_restore_{cat_id}", help="Riporta i memo selezionati tra quelli attivi", use_container_width=True):
                            ripristinati = database.imposta_stato_archiviato_multipli(selezionati, archiviato=False)
                            for m_id in selezionati:
                                st.session_state.pop(f"sel_{cat_id}_{m_id}", None)
                            st.success(f"{ripristinati} memo ripristinati tra i compiti attivi!")
                            st.rerun()
                    else:
                        st.button("↩️ Ripristina", disabled=True, key=f"btn_bulk_restore_dis_{cat_id}", use_container_width=True)
                else:
                    if n_sel > 0:
                        if st.button(f"📦 Archivia ({n_sel})", key=f"btn_bulk_arch_{cat_id}", help="Archivia i memo selezionati", use_container_width=True):
                            archiviati = database.imposta_stato_archiviato_multipli(selezionati, archiviato=True)
                            for m_id in selezionati:
                                st.session_state.pop(f"sel_{cat_id}_{m_id}", None)
                            st.success(f"{archiviati} memo archiviati con successo!")
                            st.rerun()
                    else:
                        st.button("📦 Archivia", disabled=True, key=f"btn_bulk_arch_dis_{cat_id}", use_container_width=True)

            with col_bulk_del:
                if cat_id == "Cestino":
                    if len(df_sezione) > 0:
                        with st.popover("🔥 Svuota Cestino", use_container_width=True):
                            st.markdown("⚠️ **Svuotamento Cestino**")
                            st.write("Vuoi eliminare DEFINITIVAMENTE tutti i memo presenti nel cestino? L'operazione non è reversibile.")
                            if st.button("🔥 Sì, Svuota tutto", type="primary", key=f"confirm_empty_trash_{cat_id}", use_container_width=True):
                                eliminati = database.svuota_cestino()
                                for m_id in ids_sezione:
                                    st.session_state.pop(f"sel_{cat_id}_{m_id}", None)
                                st.success(f"{eliminati} memo eliminati definitivamente!")
                                st.rerun()
                    else:
                        st.button("🔥 Cestino vuoto", disabled=True, key=f"btn_empty_trash_dis_{cat_id}", use_container_width=True)
                else:
                    if n_sel > 0:
                        with st.popover(f"🗑️ Cestina ({n_sel})", use_container_width=True):
                            st.markdown(f"🗑️ **Sposta nel Cestino**")
                            st.write(f"Vuoi spostare nel Cestino i **{n_sel}** memo selezionati?")
                            st.caption("Potrai ripristinarli in qualunque momento dalla scheda Cestino.")
                            if st.button(f"Sì, Cestina {n_sel} memo", type="primary", key=f"confirm_bulk_trash_{cat_id}", use_container_width=True):
                                cestinati = database.sposta_nel_cestino_multipli(selezionati)
                                for m_id in selezionati:
                                    st.session_state.pop(f"sel_{cat_id}_{m_id}", None)
                                st.success(f"{cestinati} memo spostati nel Cestino!")
                                st.rerun()
                    else:
                        st.button("🗑️ Cestina selezionati", disabled=True, key=f"btn_bulk_del_dis_{cat_id}", use_container_width=True)

            st.write("")

            for _, row in df_mostrati.iterrows():
                memo_id = int(row['id'])
                p_val = int(row['priorita'])
                is_trashed = int(row.get('cestinato', 0)) == 1
                is_archived = int(row.get('archiviato', 0)) == 1
                
                if is_trashed:
                    badge_p = "🗑️"
                elif is_archived:
                    badge_p = "⚪"
                elif p_val == 1:
                    badge_p = "🔴"
                elif p_val == 2:
                    badge_p = "🟡"
                else:
                    badge_p = "🟢"

                tipo_str = str(row['tipo_contenuto']).capitalize()
                cat_str = str(row['categoria'])
                titolo_memo = str(row['titolo']) or "Senza Titolo"
                data_str = str(row['data_creazione'])
                try:
                    data_corta = datetime.strptime(data_str[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
                except Exception:
                    data_corta = data_str[:10]

                promemoria_val = str(row['data_promemoria']) if (pd.notna(row['data_promemoria']) and row['data_promemoria']) else ""

                badge_agenda = f" | 📅 SCADENZA: {promemoria_val}" if promemoria_val else ""
                header_text = f"{badge_p} [{cat_str}] **{titolo_memo}** — *({tipo_str})*{badge_agenda} - {data_corta}"

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

                        allegato_file = str(row.get('allegato_path') or '').strip()
                        if allegato_file and allegato_file.lower() not in ['none', 'nan', ''] and os.path.exists(allegato_file):
                            ocr_fallito = "elaborazione ocr non riuscita" in str(row.get('testo_originale') or '').lower()
                            titolo_expander = "📷 Visualizza Immagine Allegata" + (" (⚠️ OCR non riuscito)" if ocr_fallito else "")
                            with st.expander(titolo_expander, expanded=ocr_fallito):
                                c_ocr_btn, c_dim = st.columns([1.1, 1.4], vertical_alignment="center")
                                with c_ocr_btn:
                                    if st.button("🔍 Rianalizza con OCR", key=f"btn_reocr_{row['id']}_{cat_id}", help="Esegui nuovamente il riconoscimento del testo e l'analisi AI sull'immagine"):
                                        with st.spinner("Scansione Vision in corso con Ollama..."):
                                            import vision_processor
                                            import ai_processor
                                            nuovo_testo = vision_processor.analizza_immagine(allegato_file)
                                            if nuovo_testo and "elaborazione ocr non riuscita" not in nuovo_testo.lower():
                                                analisi_ai = ai_processor.analizza_testo(nuovo_testo)
                                                database.modifica_memo(
                                                    memo_id=int(row['id']),
                                                    titolo=analisi_ai.get("titolo") or row['titolo'],
                                                    riassunto=analisi_ai.get("riassunto") or row['riassunto'],
                                                    testo_originale=nuovo_testo,
                                                    categoria=analisi_ai.get("categoria") or row['categoria'],
                                                    priorita=int(analisi_ai.get("priorita") or row['priorita']),
                                                    tags=", ".join(analisi_ai.get("tags", [])) or row['tags']
                                                )
                                                st.success("Testo estratto e riassunto AI aggiornati!")
                                                st.rerun()
                                            else:
                                                st.error("Riconoscimento fallito. Verifica che Ollama (qwen2.5vl:7b) sia attivo.")
                                with c_dim:
                                    dim_sel = st.segmented_control(
                                        "Formato:",
                                        options=["📱 Smartphone (380px)", "🖥️ Medio (540px)", "🔍 100%"],
                                        default="📱 Smartphone (380px)",
                                        key=f"dim_img_{row['id']}_{cat_id}",
                                        label_visibility="collapsed"
                                    )

                                if dim_sel == "🖥️ Medio (540px)":
                                    st.image(allegato_file, width=540, caption=f"Allegato: {titolo_memo}")
                                elif dim_sel == "🔍 100%":
                                    st.image(allegato_file, use_container_width=True, caption=f"Allegato: {titolo_memo}")
                                else:
                                    st.image(allegato_file, width=380, caption=f"Allegato: {titolo_memo}")

                        # Podcast Player & Generatore su Richiesta
                        podcast_file = str(row.get('audio_podcast_path') or '').strip()
                        if podcast_file and podcast_file.lower() not in ['none', 'nan', ''] and os.path.exists(podcast_file):
                            dur_sec = int(row.get('podcast_durata') or 0)
                            dur_m, dur_s = dur_sec // 60, dur_sec % 60
                            with st.expander(f"🎙️ Ascolta Podcast Audio ({dur_m}:{dur_s:02d})", expanded=False):
                                st.audio(podcast_file, format="audio/mp3")
                                if row.get('podcast_intro'):
                                    st.caption(f"**Intro parlata:** *\"{row['podcast_intro']}\"*")
                                
                                c_dl, c_rss = st.columns([1.2, 1.8], vertical_alignment="center")
                                with c_dl:
                                    titolo_pulito = re.sub(r'[\\/*?:"<>|]', "", str(titolo_memo or f"memo_{row['id']}"))
                                    titolo_pulito = re.sub(r'\s+', '_', titolo_pulito.strip())[:45]
                                    nome_file_mp3 = f"Memo_{row['id']}_{titolo_pulito}.mp3"
                                    try:
                                        with open(podcast_file, "rb") as f_mp3:
                                            mp3_bytes = f_mp3.read()
                                        st.download_button(
                                            label="💾 Scarica MP3",
                                            data=mp3_bytes,
                                            file_name=nome_file_mp3,
                                            mime="audio/mpeg",
                                            key=f"dl_pod_mp3_{cat_id}_{row['id']}",
                                            use_container_width=True
                                        )
                                    except Exception as e_dl:
                                        st.caption(f"⚠️ Errore file: {e_dl}")
                                with c_rss:
                                    incluso_attualmente = bool(int(row.get('podcast_incluso') or 0))
                                    nuovo_stato = st.checkbox(
                                        "Includi nel feed RSS di AntennaPod",
                                        value=incluso_attualmente,
                                        key=f"chk_feed_rss_{row['id']}_{cat_id}"
                                    )
                                    if nuovo_stato != incluso_attualmente:
                                        database.cambia_inclusione_podcast(int(row['id']), nuovo_stato)
                                        podcast_feed.genera_feed_rss()
                                        st.rerun()
                        elif row.get('link_originale') and str(row.get('link_originale')).strip().startswith(('http://', 'https://')):
                            if podcast_feed.is_memo_in_generazione(int(row['id'])):
                                st.info("⏳ Sintesi podcast in corso in background... Puoi continuare a navigare liberamente.")
                            elif st.button("🎙️ Genera Podcast Audio da Link", key=f"btn_gen_podcast_{row['id']}_{cat_id}"):
                                sett = settings_manager.carica_impostazioni()
                                voce_podcast = st.session_state.get("cfg_podcast_voice") or sett.get("podcast_voice", "im_nicola")
                                speed_podcast = float(st.session_state.get("cfg_podcast_speed") or sett.get("podcast_speed", 1.0))
                                podcast_feed.avvia_job_podcast_da_link(
                                    memo_id=int(row['id']),
                                    link_originale=str(row['link_originale']).strip(),
                                    titolo_corrente=str(row.get('titolo') or ''),
                                    categoria_corrente=str(row.get('categoria') or 'Web'),
                                    voce_scelta=voce_podcast,
                                    speed_podcast=speed_podcast
                                )
                                st.rerun()
                        
                        if row['tags']:
                            tags_list = [f"`{t.strip()}`" for t in str(row['tags']).split(',') if t.strip()]
                            st.markdown("**Tags:** " + " ".join(tags_list))

                        st.markdown("---")

                        # BARRA DELLE AZIONI
                        if is_trashed:
                            col_share, col_ripristina, col_elimina_def = st.columns([1.5, 1.4, 1.4])

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

                            with col_ripristina:
                                if st.button("↩️ Ripristina Memo", key=f"btn_res_trash_{cat_id}_{memo_id}", help="Ripristina questo memo dal cestino", use_container_width=True):
                                    database.ripristina_dal_cestino(memo_id)
                                    st.session_state.pop(f"sel_{cat_id}_{memo_id}", None)
                                    st.success("Memo ripristinato dal Cestino!")
                                    st.rerun()

                            with col_elimina_def:
                                with st.popover("🔥 Elimina per Sempre"):
                                    st.write(f"Vuoi eliminare definitivamente questo memo #{memo_id}?")
                                    st.caption("⚠️ Questa azione è irreversibile. Verranno eliminati anche eventuali allegati.")
                                    if st.button("Sì, Elimina Definitivamente", key=f"del_def_{cat_id}_{memo_id}", type="primary"):
                                        if database.elimina_memo(memo_id):
                                            st.session_state.pop(f"sel_{cat_id}_{memo_id}", None)
                                            st.success("Memo eliminato definitivamente!")
                                            st.rerun()
                                        else:
                                            st.error("Errore eliminazione.")

                        else:
                            col_share, col_azioni, col_archivia, col_elimina = st.columns([1.5, 1.3, 1.4, 1.1])

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

                            with col_azioni:
                                if st.button("✏️ Modifica", key=f"btn_open_edit_{cat_id}_{memo_id}", use_container_width=True):
                                    dialog_modifica_memo(row.to_dict())

                            with col_archivia:
                                if is_archived:
                                    if st.button("↩️ Ripristina", key=f"btn_res_single_{cat_id}_{memo_id}", help="Riporta questo memo tra i compiti attivi", use_container_width=True):
                                        database.imposta_stato_archiviato(memo_id, archiviato=False)
                                        st.success("Memo ripristinato tra i compiti attivi!")
                                        st.rerun()
                                else:
                                    if st.button("📦 Archivia", key=f"btn_arch_single_{cat_id}_{memo_id}", help="Archivia questo memo completato", use_container_width=True):
                                        database.imposta_stato_archiviato(memo_id, archiviato=True)
                                        st.success("Memo archiviato con successo!")
                                        st.rerun()

                            with col_elimina:
                                with st.popover("🗑️ Cestina"):
                                    st.write(f"Vuoi spostare questo memo #{memo_id} nel Cestino?")
                                    st.caption("Potrai ripristinarlo in qualunque momento dalla scheda Cestino.")
                                    if st.button("Sì, Cestina", key=f"trash_{cat_id}_{memo_id}", type="primary"):
                                        if database.sposta_nel_cestino(memo_id):
                                            st.session_state.pop(f"sel_{cat_id}_{memo_id}", None)
                                            st.success("Memo spostato nel Cestino!")
                                            st.rerun()
                                        else:
                                            st.error("Errore nello spostamento.")

            # Banner e scorciatoia per caricare altri elementi quando la vista è limitata
            if len(df_sezione) > len(df_mostrati):
                st.markdown("---")
                c_m1, c_m2, c_m3 = st.columns([2.5, 1, 1], vertical_alignment="center")
                with c_m1:
                    st.caption(f"Visualizzazione limitata ai primi **{len(df_mostrati)}** memo su **{len(df_sezione)}** per garantire la massima reattività.")
                with c_m2:
                    if limite_n < 50 and len(df_sezione) > 25:
                        if st.button("Mostra 50", key=f"btn_m50_{cat_id}", use_container_width=True):
                            st.session_state["cfg_memo_limit"] = "50 memo"
                            st.rerun()
                with c_m3:
                    if st.button(f"Mostra Tutti ({len(df_sezione)})", key=f"btn_mall_{cat_id}", use_container_width=True):
                        st.session_state["cfg_memo_limit"] = "Tutti"
                        st.rerun()