import os
import re
import socket
import threading
from datetime import datetime
import email.utils
import xml.etree.ElementTree as ET
from xml.dom import minidom
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import qrcode
import database

PODCAST_DIR = os.path.join(os.path.dirname(__file__), "podcasts")
os.makedirs(PODCAST_DIR, exist_ok=True)

FEED_XML_PATH = os.path.join(PODCAST_DIR, "feed.xml")
QR_CODE_PATH = os.path.join(PODCAST_DIR, "podcast_qr.png")
COVER_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "LOGO_TONDO_NERO.png")

FEED_PORT = 8503
_SERVER_THREAD = None
_SERVER_INSTANCE = None

def ottieni_ip_locale() -> str:
    """Rileva l'indirizzo IP locale (LAN/Wi-Fi) del computer."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Non invia traffico reale, serve solo al kernel per risolvere l'interfaccia di rete primaria
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def formatta_data_rfc822(data_str: str) -> str:
    """Converte una data (YYYY-MM-DD HH:MM:SS) in formato RFC-822 standard per feed RSS podcast."""
    try:
        dt = datetime.strptime(str(data_str)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        dt = datetime.now()
    return email.utils.format_datetime(dt)

def genera_feed_rss(porta: int = FEED_PORT) -> str:
    """
    Costruisce e salva su disco il file feed.xml conforme alle specifiche RSS 2.0 / iTunes Podcast.
    Restituisce l'URL completo del feed per AntennaPod.
    """
    ip_lan = ottieni_ip_locale()
    base_url = f"http://{ip_lan}:{porta}"
    feed_url = f"{base_url}/feed.xml"

    memo_podcast = database.ottieni_memo_podcast(solo_inclusi=True)

    rss = ET.Element("rss", {
        "version": "2.0",
        "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "xmlns:content": "http://purl.org/rss/1.0/modules/content/"
    })

    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Astro_KW MemoBot Podcast"
    ET.SubElement(channel, "link").text = feed_url
    ET.SubElement(channel, "description").text = (
        "I tuoi articoli e approfondimenti web raccolti da mobile e letti ad alta voce con AI locale per l'ascolto su Android Auto."
    )
    ET.SubElement(channel, "language").text = "it-it"
    ET.SubElement(channel, "itunes:author").text = "Astro_KW MemoBot"
    ET.SubElement(channel, "itunes:summary").text = "Notiziario e rassegna articoli personali per l'auto."
    
    # Categoria iTunes
    cat = ET.SubElement(channel, "itunes:category", {"text": "News"})
    ET.SubElement(cat, "itunes:category", {"text": "Tech News"})
    
    # Immagine di copertina del Podcast
    ET.SubElement(channel, "itunes:image", {"href": f"{base_url}/cover.png"})
    
    img_tag = ET.SubElement(channel, "image")
    ET.SubElement(img_tag, "url").text = f"{base_url}/cover.png"
    ET.SubElement(img_tag, "title").text = "Astro_KW MemoBot Podcast"
    ET.SubElement(img_tag, "link").text = feed_url

    # Inserimento episodi
    for m in memo_podcast:
        audio_rel = m.get("audio_podcast_path") or ""
        audio_filename = os.path.basename(audio_rel)
        audio_path_abs = os.path.join(PODCAST_DIR, audio_filename) if not os.path.isabs(audio_rel) else audio_rel

        if not os.path.exists(audio_path_abs):
            continue

        file_size = os.path.getsize(audio_path_abs)
        audio_url = f"{base_url}/episodes/{urllib.parse.quote(audio_filename)}"

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = m.get("titolo") or "Articolo MemoBot"
        
        # Descrizione dettagliata (intro + link alla fonte)
        desc_text = m.get("podcast_intro") or m.get("riassunto") or ""
        if m.get("link_originale"):
            desc_text += f"\n\nFonte originale: {m['link_originale']}"
        ET.SubElement(item, "description").text = desc_text
        
        if m.get("link_originale"):
            ET.SubElement(item, "link").text = m["link_originale"]

        ET.SubElement(item, "pubDate").text = formatta_data_rfc822(m.get("data_creazione"))
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = f"memobot-podcast-{m['id']}"
        
        # Enclosure audio vitale per AntennaPod / Android Auto
        ET.SubElement(item, "enclosure", {
            "url": audio_url,
            "length": str(file_size),
            "type": "audio/mpeg"
        })

        durata_sec = m.get("podcast_durata") or 60
        ET.SubElement(item, "itunes:duration").text = str(durata_sec)
        ET.SubElement(item, "itunes:author").text = m.get("categoria", "Notizie")

    # Serializzazione XML formattata con indentazione
    xml_str = ET.tostring(rss, encoding="utf-8")
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ", encoding="utf-8")

    with open(FEED_XML_PATH, "wb") as f:
        f.write(pretty_xml)

    # Genera anche il QR Code aggiornato per AntennaPod
    genera_qr_code(feed_url)

    print(f"[PODCAST_FEED] Feed RSS aggiornato ({len(memo_podcast)} episodi): {feed_url}")
    return feed_url

def genera_qr_code(url: str, output_path: str = QR_CODE_PATH):
    """Genera un QR Code in formato PNG per scansionare il feed direttamente con lo smartphone."""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
    except Exception as e:
        print(f"[PODCAST_FEED] Avviso generazione QR code: {e}")

class PodcastHTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    Gestore HTTP dedicato che serve il feed RSS, l'immagine di copertina
    e lo streaming dei file MP3 con pieno supporto HTTP Range (206 Partial Content).
    """
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/feed.xml", "/podcast.xml", "/"]:
            # Rigenera sempre il feed al volo per inviare lo stato più recente da database
            genera_feed_rss(FEED_PORT)
            
            with open(FEED_XML_PATH, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
            return

        elif path == "/cover.png":
            cover_file = COVER_IMAGE_PATH if os.path.exists(COVER_IMAGE_PATH) else None
            if cover_file:
                with open(cover_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        elif path == "/qr.png":
            if os.path.exists(QR_CODE_PATH):
                with open(QR_CODE_PATH, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        elif path.startswith("/episodes/"):
            # Streaming file audio con supporto Range per AntennaPod
            filename = urllib.parse.unquote(path.replace("/episodes/", ""))
            filepath = os.path.join(PODCAST_DIR, filename)

            if not os.path.exists(filepath):
                self.send_error(404, "Episodio podcast non trovato")
                return

            # Supporto per richieste HTTP Range (cruciale per seeking e resume su Android Auto)
            file_size = os.path.getsize(filepath)
            range_header = self.headers.get("Range")

            if range_header:
                # Esempio: "bytes=1000-2000" o "bytes=1000-"
                m = re.match(r"bytes=(\d+)-(\d*)", range_header)
                if m:
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else file_size - 1
                    end = min(end, file_size - 1)
                    length = end - start + 1

                    self.send_response(206)
                    self.send_header("Content-Type", "audio/mpeg")
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()

                    with open(filepath, "rb") as f:
                        f.seek(start)
                        self.wfile.write(f.read(length))
                    return

            # Risposta completa (senza Range)
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with open(filepath, "rb") as f:
                self.wfile.write(f.read())
            return

        self.send_error(404, "Percorso non valido")

    def log_message(self, format, *args):
        # Silenzia i log HTTP continui per non inquinare la console
        pass

def avvia_server_podcast_background(porta: int = FEED_PORT):
    """Avvia il server HTTP per AntennaPod in un thread demone non bloccante."""
    global _SERVER_THREAD, _SERVER_INSTANCE
    if _SERVER_THREAD is not None and _SERVER_THREAD.is_alive():
        return f"http://{ottieni_ip_locale()}:{porta}/feed.xml"

    genera_feed_rss(porta)

    try:
        _SERVER_INSTANCE = ThreadingHTTPServer(("0.0.0.0", porta), PodcastHTTPRequestHandler)
        _SERVER_THREAD = threading.Thread(target=_SERVER_INSTANCE.serve_forever, daemon=True)
        _SERVER_THREAD.start()
        print(f"[PODCAST_FEED] 🚀 Server HTTP Podcast attivo in background su porta {porta}!")
    except Exception as e:
        print(f"[PODCAST_FEED] Avviso avvio server (porta {porta}): {e}")

    return f"http://{ottieni_ip_locale()}:{porta}/feed.xml"

def render_scheda_podcast(df_memo=None):
    """Renderizza l'interfaccia interattiva della scheda Podcast in Streamlit."""
    import streamlit as st
    import settings_manager
    import podcast_tts
    import podcast_scraper

    feed_url = avvia_server_podcast_background(FEED_PORT)
    settings = settings_manager.carica_impostazioni()

    st.markdown("""
    <div style="padding: 10px 0 15px 0;">
        <h2 style="margin: 0; font-size: 1.8rem; font-weight: 700; color: inherit; display: flex; align-items: center; flex-wrap: wrap; gap: 10px;">
            <span>🎙️ Astro_KW MemoBot Podcast</span>
            <span style="font-size: 0.85rem; font-weight: 500; padding: 4px 12px; border-radius: 20px; background: rgba(128, 128, 128, 0.15); border: 1px solid rgba(128, 128, 128, 0.25);">
                📻 Per Android Auto & AntennaPod
            </span>
        </h2>
        <p style="margin: 6px 0 0 0; opacity: 0.85; font-size: 1.0rem;">
            I tuoi articoli web convertiti in rassegna audio personale: intro da 30 secondi con sintesi parlata, lettura integrale e ascolto offline in auto.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # BOX CONNESSIONE ANTENNAPOD & QR CODE
    # --------------------------------------------------------------------------
    with st.container(border=True):
        col_info, col_qr = st.columns([2.5, 1.2], vertical_alignment="center")

        with col_info:
            st.markdown("#### 📱 Connetti con AntennaPod (Android Auto)")
            st.markdown(f"""
            1. Apri **AntennaPod** sul tuo smartphone mentre sei collegato al Wi-Fi di casa.
            2. Tocca **Aggiungi Podcast** ➔ **Aggiungi da indirizzo RSS**.
            3. Inquadra il **QR Code** qui a destra oppure incolla il seguente indirizzo:
            """)
            st.code(feed_url, language="text")
            
            c_btn1, c_btn2 = st.columns([1.3, 1.3])
            with c_btn1:
                if st.button("🔄 Rigenera Feed RSS", use_container_width=True):
                    genera_feed_rss(FEED_PORT)
                    st.success("Feed RSS aggiornato!")
                    st.rerun()
            with c_btn2:
                with st.popover("⚙️ Impostazioni Voce & TTS", use_container_width=True):
                    st.markdown("##### ⚙️ Configurazione Voce")
                    
                    import podcast_tts
                    voci_totali = podcast_tts.elenca_voci_disponibili()
                    curr_voice = settings.get("podcast_voice", "im_nicola")
                    if curr_voice not in voci_totali:
                        curr_voice = "im_nicola"

                    sel_voice = st.selectbox(
                        "Voce Narrante:",
                        options=list(voci_totali.keys()),
                        format_func=lambda x: voci_totali[x],
                        index=list(voci_totali.keys()).index(curr_voice),
                        key="pop_voice_select"
                    )

                    with st.expander("➕ Aggiungi Nuovo Campione Voce", expanded=False):
                        st.caption("Carica un audio di 10–25s (senza musica) per clonare una nuova voce con la GPU:")
                        up_voice_pop = st.file_uploader("Audio (.wav/.mp3):", type=["wav", "mp3", "ogg", "flac"], key="upl_voice_pop")
                        nome_v_pop = st.text_input("Nome della voce (es. Alberto Angela):", key="txt_v_pop")
                        if st.button("Salva Nuova Voce", key="btn_save_v_pop", type="primary"):
                            if up_voice_pop and nome_v_pop.strip():
                                clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', nome_v_pop.strip().lower())
                                ext = os.path.splitext(up_voice_pop.name)[1].lower()
                                target_p = os.path.join(podcast_tts.VOCI_DIR, f"{clean_name}{ext}")
                                with open(target_p, "wb") as f_v:
                                    f_v.write(up_voice_pop.read())
                                st.success(f"Voce '{nome_v_pop.strip()}' aggiunta!")
                                st.rerun()

                    curr_speed = float(settings.get("podcast_speed", 1.0))
                    sel_speed = st.slider("Velocità di lettura:", min_value=0.85, max_value=1.25, value=curr_speed, step=0.05, key="pop_speed_slider")

                    auto_gen = st.checkbox("Genera podcast in automatico all'arrivo di link", value=settings.get("podcast_auto_generate", True), key="pop_auto_chk")

                    if st.button("💾 Salva Impostazioni Podcast", type="primary", use_container_width=True, key="pop_btn_save_cfg"):
                        if sel_voice.startswith("clone:"):
                            settings["podcast_engine"] = "xtts"
                        elif "Neural" in sel_voice:
                            settings["podcast_engine"] = "edge"
                        else:
                            settings["podcast_engine"] = "kokoro"
                        settings["podcast_voice"] = sel_voice
                        settings["podcast_speed"] = sel_speed
                        settings["podcast_auto_generate"] = auto_gen
                        settings_manager.salva_impostazioni(settings)
                        st.success("Impostazioni salvate con successo!")
                        st.rerun()

        with col_qr:
            if os.path.exists(QR_CODE_PATH):
                st.image(QR_CODE_PATH, caption="Inquadra con AntennaPod", use_container_width=True)
            else:
                genera_qr_code(feed_url)
                if os.path.exists(QR_CODE_PATH):
                    st.image(QR_CODE_PATH, caption="Inquadra con AntennaPod", use_container_width=True)

    st.markdown("---")

    # --------------------------------------------------------------------------
    # LISTA EPISODI DEL PODCAST
    # --------------------------------------------------------------------------
    episodi = database.ottieni_memo_podcast(solo_inclusi=False)

    st.subheader(f"📻 Episodi Generati ({len(episodi)})")

    if not episodi:
        st.info("Nessun episodio podcast ancora presente. Invia un link di un articolo su Telegram per generare il tuo primo episodio, oppure converti un memo qui sotto!")
    else:
        # Calcolo elementi selezionati per le azioni massive
        ids_episodi = [int(ep["id"]) for ep in episodi]
        selezionati = [m_id for m_id in ids_episodi if st.session_state.get(f"sel_pod_{m_id}", False)]
        n_sel = len(selezionati)

        # Toolbar di Selezione e Azioni Massive
        col_info, col_all, col_none, col_feed_incl, col_feed_excl, col_bulk_del = st.columns(
            [2.2, 1.0, 1.0, 1.8, 1.8, 2.0], vertical_alignment="center"
        )

        with col_info:
            st.write(f"Mostrati **{len(episodi)}** | **{n_sel}** selezionati")

        with col_all:
            if st.button("☑️ Tutti", key="btn_all_pod", help="Seleziona tutti gli episodi", use_container_width=True):
                for m_id in ids_episodi:
                    st.session_state[f"sel_pod_{m_id}"] = True
                st.rerun()

        with col_none:
            if st.button("⬜ Nessuno", key="btn_none_pod", help="Deseleziona tutti", use_container_width=True):
                for m_id in ids_episodi:
                    st.session_state[f"sel_pod_{m_id}"] = False
                st.rerun()

        with col_feed_incl:
            if n_sel > 0:
                if st.button(f"➕ Nel Feed ({n_sel})", key="btn_bulk_incl_pod", help="Includi gli episodi selezionati nel feed AntennaPod", use_container_width=True):
                    database.cambia_inclusione_podcast_multipli(selezionati, incluso=True)
                    genera_feed_rss(FEED_PORT)
                    st.success(f"{n_sel} episodi inclusi nel feed!")
                    st.rerun()
            else:
                st.button("➕ Nel Feed", disabled=True, key="btn_bulk_incl_pod_dis", use_container_width=True)

        with col_feed_excl:
            if n_sel > 0:
                if st.button(f"⏸️ Escludi ({n_sel})", key="btn_bulk_excl_pod", help="Escludi gli episodi selezionati dal feed AntennaPod", use_container_width=True):
                    database.cambia_inclusione_podcast_multipli(selezionati, incluso=False)
                    genera_feed_rss(FEED_PORT)
                    st.success(f"{n_sel} episodi esclusi dal feed!")
                    st.rerun()
            else:
                st.button("⏸️ Escludi", disabled=True, key="btn_bulk_excl_pod_dis", use_container_width=True)

        with col_bulk_del:
            if n_sel > 0:
                with st.popover(f"🗑️ Elimina ({n_sel})", use_container_width=True):
                    st.write(f"Vuoi eliminare definitivamente i file audio di **{n_sel}** podcast selezionati?")
                    st.caption("I memo testuali (link, riassunti e note) rimarranno conservati nel database.")
                    if st.button(f"Sì, Elimina {n_sel} Audio", key="btn_confirm_bulk_del_pod", type="primary", use_container_width=True):
                        eliminati = database.rimuovi_podcast_multipli(selezionati)
                        for m_id in selezionati:
                            st.session_state.pop(f"sel_pod_{m_id}", None)
                        genera_feed_rss(FEED_PORT)
                        st.success(f"{eliminati} file audio podcast eliminati con successo!")
                        st.rerun()
            else:
                st.button("🗑️ Elimina", disabled=True, key="btn_bulk_del_pod_dis", use_container_width=True)

        st.markdown("")

        for ep in episodi:
            memo_id = ep["id"]
            titolo = ep.get("titolo") or "Senza Titolo"
            fonte = ep.get("categoria") or "Web"
            durata_sec = int(ep.get("podcast_durata") or 0)
            durata_str = f"{durata_sec // 60}m {durata_sec % 60}s" if durata_sec >= 60 else f"{durata_sec}s"
            data_creazione = str(ep.get("data_creazione", ""))[:16]
            incluso_feed = bool(ep.get("podcast_incluso", 1))

            audio_rel = ep.get("audio_podcast_path")
            audio_abs = os.path.join(PODCAST_DIR, os.path.basename(audio_rel)) if audio_rel else None

            with st.container(border=True):
                c_sel, c_title, c_meta, c_badge = st.columns([0.35, 3.2, 1.6, 1], vertical_alignment="center")
                with c_sel:
                    st.checkbox(
                        "",
                        key=f"sel_pod_{memo_id}",
                        label_visibility="collapsed"
                    )
                with c_title:
                    st.markdown(f"#### 🎧 #{memo_id} — {titolo}")
                with c_meta:
                    st.caption(f"📁 {fonte} | 🕒 {durata_str} | 📅 {data_creazione}")
                with c_badge:
                    if incluso_feed:
                        st.success("📻 Nel Feed")
                    else:
                        st.warning("⏸️ Escluso")

                if ep.get("podcast_intro"):
                    st.markdown(f"**Intro parlata (30s):** *\"{ep['podcast_intro']}\"*")

                if audio_abs and os.path.exists(audio_abs):
                    st.audio(audio_abs, format="audio/mp3")

                c_act1, c_act2, c_act3, c_act4 = st.columns([1.6, 1.4, 1.4, 2.6], vertical_alignment="center")
                with c_act1:
                    btn_label = "⏸️ Escludi da AntennaPod" if incluso_feed else "➕ Includi nel Feed"
                    if st.button(btn_label, key=f"btn_toggle_feed_{memo_id}", use_container_width=True):
                        database.cambia_inclusione_podcast(memo_id, not incluso_feed)
                        genera_feed_rss(FEED_PORT)
                        st.rerun()

                with c_act2:
                    titolo_pulito = re.sub(r'[\\/*?:"<>|]', "", str(titolo or f"podcast_{memo_id}"))
                    titolo_pulito = re.sub(r'\s+', '_', titolo_pulito.strip())[:45]
                    nome_file_mp3 = f"Podcast_{memo_id}_{titolo_pulito}.mp3"
                    try:
                        with open(audio_abs, "rb") as f_mp3:
                            mp3_bytes = f_mp3.read()
                        st.download_button(
                            "💾 Scarica MP3",
                            data=mp3_bytes,
                            file_name=nome_file_mp3,
                            mime="audio/mpeg",
                            key=f"dl_pod_tab_{memo_id}",
                            use_container_width=True
                        )
                    except Exception as e_dl:
                        st.caption(f"⚠️ Errore file: {e_dl}")

                with c_act3:
                    with st.popover("🗑️ Elimina Audio", use_container_width=True):
                        st.write("Vuoi cancellare definitivamente il file audio di questo podcast?")
                        if st.button("Sì, Elimina", key=f"btn_del_pod_{memo_id}", type="primary", use_container_width=True):
                            database.rimuovi_podcast_memo(memo_id)
                            st.session_state.pop(f"sel_pod_{memo_id}", None)
                            genera_feed_rss(FEED_PORT)
                            st.rerun()

    # --------------------------------------------------------------------------
    # CREAZIONE PODCAST DA TESTO LIBERO / APPUNTI PC
    # --------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("✍️ Crea Podcast Audio da Testo Libero, PDF o Appunti (PC)", expanded=False):
        st.write("Incolla un testo oppure **carica direttamente un PDF o un'immagine** per estrarre il contenuto e trasformarlo in un episodio podcast per l'ascolto in auto:")

        def _cb_incolla_clipboard():
            from PIL import Image, ImageGrab
            import io
            import podcast_scraper

            try:
                clip_data = ImageGrab.grabclipboard()
            except Exception as e:
                st.session_state["_clip_msg"] = f"⚠️ Errore lettura appunti: {e}"
                return

            img_bytes = None
            filename_mock = f"screenshot_{datetime.now().strftime('%H%M%S')}.png"

            if isinstance(clip_data, Image.Image):
                buf = io.BytesIO()
                clip_data.convert("RGB").save(buf, format="PNG")
                img_bytes = buf.getvalue()
            elif isinstance(clip_data, list) and clip_data:
                first_file = clip_data[0]
                if os.path.exists(first_file) and os.path.splitext(first_file)[1].lower() in [".png", ".jpg", ".jpeg", ".webp", ".pdf"]:
                    with open(first_file, "rb") as f:
                        img_bytes = f.read()
                    filename_mock = os.path.basename(first_file)

            if not img_bytes:
                st.session_state["_clip_msg"] = "⚠️ Negli appunti non c'è un'immagine o screenshot. Cattura prima una porzione di schermo con Win+Shift+S (Cattura Schermo) o copia un'immagine!"
                return

            testo_estr, tit_sugg = podcast_scraper.estrai_testo_da_documento(img_bytes, filename_mock)
            if testo_estr and testo_estr.strip():
                testo_attuale = st.session_state.get("txt_pod_manual_body", "")
                accoda = st.session_state.get("chk_upl_accoda_testo", True)
                if accoda and testo_attuale.strip():
                    st.session_state["txt_pod_manual_body"] = testo_attuale.strip() + "\n\n" + testo_estr.strip()
                else:
                    st.session_state["txt_pod_manual_body"] = testo_estr.strip()
                if not st.session_state.get("txt_pod_manual_title") and tit_sugg:
                    st.session_state["txt_pod_manual_title"] = tit_sugg
                st.session_state["_clip_msg"] = f"✅ Screenshot ({len(img_bytes)//1024} KB) incollato ed elaborato con successo ({len(testo_estr)} caratteri estratti)!"
            else:
                st.session_state["_clip_msg"] = "⚠️ OCR completato ma non è stato possibile estrarre testo dall'immagine incollata."

        with st.expander("📂 Carica PDF / Screenshot o Incolla da Appunti (Win+Shift+S / Ctrl+V)", expanded=True):
            c_clip1, c_clip2 = st.columns([1.8, 1.2], vertical_alignment="center")
            with c_clip1:
                st.button(
                    "📋 Incolla Schermata da Appunti (Win+Shift+S / Ctrl+V)",
                    key="btn_paste_from_clipboard",
                    on_click=_cb_incolla_clipboard,
                    use_container_width=True,
                    help="Estrae il testo dallo screenshot attualmente presente negli appunti (catturato con Win+Shift+S o Stamp) senza dover salvare alcun file su disco!"
                )
            with c_clip2:
                accoda_testo = st.checkbox(
                    "➕ Accoda al testo esistente",
                    value=True,
                    key="chk_upl_accoda_testo",
                    help="Se attivo, il testo estratto dalle nuove pagine o file verrà aggiunto in fondo a quello già presente anziché sostituirlo."
                )

            if "_clip_msg" in st.session_state and st.session_state["_clip_msg"]:
                msg_clip = st.session_state.pop("_clip_msg")
                if "✅" in msg_clip:
                    st.success(msg_clip)
                else:
                    st.warning(msg_clip)

            st.caption("💡 **Scorciatoia rapidissima**: fai **Win + Shift + S**, seleziona la parte dell'articolo che vuoi ascoltare, e premi il pulsante sopra (oppure premi **Ctrl+V** sulla pagina)! Non serve salvare file su disco.")

            # Listener JavaScript globale per intercettare Ctrl+V con immagini
            import streamlit.components.v1 as components
            components.html("""
            <script>
            (function() {
                try {
                    const parentDoc = window.parent.document;
                    if (!parentDoc || parentDoc.__memobot_paste_listener_attached) return;
                    parentDoc.__memobot_paste_listener_attached = true;

                    parentDoc.addEventListener('paste', function(e) {
                        const items = (e.clipboardData || window.clipboardData)?.items;
                        let hasImg = false;
                        if (items) {
                            for (let i = 0; i < items.length; i++) {
                                if (items[i].type && items[i].type.indexOf('image') !== -1) {
                                    hasImg = true;
                                    break;
                                }
                            }
                        }
                        if (hasImg) {
                            const btns = parentDoc.querySelectorAll('button');
                            for (let b of btns) {
                                if (b.innerText && b.innerText.includes("Incolla Schermata")) {
                                    b.click();
                                    break;
                                }
                            }
                        }
                    });
                } catch (err) {
                    // Ignora eventuali restrizioni di frame cross-origin
                }
            })();
            </script>
            """, height=0)

            up_docs = st.file_uploader(
                "Oppure trascina qui uno o più documenti PDF o immagini salvate:",
                type=["pdf", "png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key="upl_doc_podcast"
            )

            if up_docs:
                processed_set = set(st.session_state.get("processed_podcast_docs", []))
                nuovi_files = [f for f in up_docs if f"{f.name}_{f.size}" not in processed_set]

                if nuovi_files:
                    # Mantiene l'ordine esatto di arrivo / selezione dell'utente
                    testi_estratti = []
                    titolo_primo = None
                    import podcast_scraper

                    progress_placeholder = st.empty()
                    for idx, doc_file in enumerate(nuovi_files):
                        progress_placeholder.info(f"⏳ Elaborazione ({idx + 1}/{len(nuovi_files)}): '{doc_file.name}'...")
                        file_bytes = doc_file.read()
                        testo_estr, tit_sugg = podcast_scraper.estrai_testo_da_documento(file_bytes, doc_file.name)
                        if testo_estr and testo_estr.strip():
                            testi_estratti.append(testo_estr.strip())
                            if not titolo_primo and tit_sugg:
                                titolo_primo = tit_sugg
                        processed_set.add(f"{doc_file.name}_{doc_file.size}")

                    progress_placeholder.empty()

                    if testi_estratti:
                        blocco_nuovo = "\n\n".join(testi_estratti)
                        testo_attuale = st.session_state.get("txt_pod_manual_body", "")

                        if accoda_testo and testo_attuale.strip():
                            st.session_state["txt_pod_manual_body"] = testo_attuale.strip() + "\n\n" + blocco_nuovo
                        else:
                            st.session_state["txt_pod_manual_body"] = blocco_nuovo

                        if not st.session_state.get("txt_pod_manual_title") and titolo_primo:
                            st.session_state["txt_pod_manual_title"] = titolo_primo

                        st.session_state["processed_podcast_docs"] = list(processed_set)
                        st.success(f"✅ Estratti con successo {len(blocco_nuovo)} caratteri da {len(testi_estratti)} documento/i!")
                        st.rerun()
                    else:
                        st.session_state["processed_podcast_docs"] = list(processed_set)
                        st.error("Impossibile estrarre testo dai file selezionati.")
            else:
                if "processed_podcast_docs" in st.session_state and st.session_state["processed_podcast_docs"]:
                    st.session_state["processed_podcast_docs"] = []

        c_tit, c_fonte = st.columns([2.5, 1])
        with c_tit:
            titolo_manuale = st.text_input("Titolo dell'episodio (facoltativo):", placeholder="Es: Appunti Strategia 2026 / Capitolo 1", key="txt_pod_manual_title")
        with c_fonte:
            fonte_manuale = st.text_input("Fonte / Autore:", value="Appunti PC", key="txt_pod_manual_fonte")

        testo_manuale = st.text_area("Testo completo da narrare a voce:", height=200, placeholder="Incolla qui il testo del documento, dell'articolo o degli appunti...", key="txt_pod_manual_body")

        def _cb_distendi_paragrafi():
            cur = st.session_state.get("txt_pod_manual_body", "")
            if cur and cur.strip():
                import podcast_scraper
                st.session_state["txt_pod_manual_body"] = podcast_scraper.ricomponi_testo_pdf(cur)

        def _cb_pulisci_citazioni():
            cur = st.session_state.get("txt_pod_manual_body", "")
            if cur and cur.strip():
                import podcast_scraper
                st.session_state["txt_pod_manual_body"] = podcast_scraper.rimuovi_citazioni_scientifiche(cur)

        def _cb_ottimizza_entrambi():
            cur = st.session_state.get("txt_pod_manual_body", "")
            if cur and cur.strip():
                import podcast_scraper
                t1 = podcast_scraper.ricomponi_testo_pdf(cur)
                st.session_state["txt_pod_manual_body"] = podcast_scraper.rimuovi_citazioni_scientifiche(t1)

        c_opt1, c_opt2 = st.columns([1.3, 1.7], vertical_alignment="center")
        with c_opt1:
            fix_pdf = st.checkbox(
                "📄 Ricostruisci paragrafi (unisci a-capo da PDF)",
                value=True,
                key="chk_fix_pdf_manual",
                help="Elimina i ritorni a capo artificiali tipici del copia-incolla da colonne PDF, fondendo le frasi per una lettura fluida"
            )
        with c_opt2:
            clean_cit = st.checkbox(
                "🎓 Rimuovi citazioni accademiche [1,2] e (Autore, Anno)",
                value=True,
                key="chk_clean_cit_manual",
                help="Elimina automaticamente note numeriche [1] e citazioni bibliografiche tipo (UNESCO, 2015; Coffee, 2022) per una lettura fluida da saggio"
            )

        c_tidy1, c_tidy2, c_tidy3 = st.columns([1, 1, 1.1])
        with c_tidy1:
            st.button(
                "🧹 Distendi Paragrafi",
                key="btn_tidy_pdf_text",
                on_click=_cb_distendi_paragrafi,
                use_container_width=True,
                help="Elimina subito gli a-capo spuri dal riquadro di testo sopra"
            )
        with c_tidy2:
            st.button(
                "🎓 Pulisci Citazioni",
                key="btn_clean_citations_now",
                on_click=_cb_pulisci_citazioni,
                use_container_width=True,
                help="Rimuove subito le parentesi di citazione [1,2] e (Autore, Anno) dal riquadro sopra"
            )
        with c_tidy3:
            st.button(
                "✨ Ottimizza Entrambi",
                key="btn_tidy_all_now",
                on_click=_cb_ottimizza_entrambi,
                use_container_width=True,
                help="Esegue sia la distensione dei paragrafi che la rimozione delle citazioni in un colpo solo"
            )

        c_voce, c_btn = st.columns([2, 1.3], vertical_alignment="bottom")
        with c_voce:
            import podcast_tts
            voci_elenco = podcast_tts.elenca_voci_disponibili()
            voce_default = st.session_state.get("cfg_podcast_voice") or settings.get("podcast_voice", "it-IT-ElsaNeural")
            if voce_default not in voci_elenco:
                voce_default = "it-IT-ElsaNeural" if "it-IT-ElsaNeural" in voci_elenco else list(voci_elenco.keys())[0]

            idx_v = list(voci_elenco.keys()).index(voce_default)
            voce_scelta = st.selectbox(
                "Scegli Voce Narrante:",
                options=list(voci_elenco.keys()),
                format_func=lambda k: voci_elenco.get(k, k),
                index=idx_v,
                key="sel_pod_manual_voice"
            )
        with c_btn:
            if st.button("🎙️ Genera Podcast da Testo", key="btn_gen_manual_podcast", type="primary", use_container_width=True):
                if not testo_manuale.strip():
                    st.warning("Inserisci o incolla del testo prima di generare il podcast.")
                else:
                    with st.spinner("Creazione memo e sintesi vocale in corso..."):
                        import podcast_scraper
                        testo_effettivo = podcast_scraper.ricomponi_testo_pdf(testo_manuale) if fix_pdf else testo_manuale
                        if clean_cit:
                            testo_effettivo = podcast_scraper.rimuovi_citazioni_scientifiche(testo_effettivo)

                        tit_eff = titolo_manuale.strip()
                        if not tit_eff:
                            prime_righe = [r.strip() for r in testo_effettivo.split('\n') if r.strip()]
                            tit_eff = prime_righe[0][:60] if prime_righe else "Podcast da Appunti"

                        fonte_eff = fonte_manuale.strip() or "Appunti PC"

                        # 1. Intro radiofonica snella (Opzione A)
                        data_str = podcast_scraper.data_corrente_parlata()
                        intro_parlata = f"Oggi è {data_str}. Da {fonte_eff}: {tit_eff}. Buon ascolto, segue il testo completo."
                        intro_norm = podcast_scraper.pulisci_testo_per_voce(intro_parlata)
                        corpo_norm = podcast_scraper.pulisci_testo_per_voce(testo_effettivo)
                        narrazione_completa = f"{intro_norm}\n\n{corpo_norm}"

                        # 2. Analisi AI per riassunto e categorizzazione archivio
                        try:
                            import ai_processor
                            analisi_ai = ai_processor.analizza_testo(testo_effettivo, titolo_suggerito=tit_eff)
                            riassunto_memo = analisi_ai.get("riassunto") or f"Podcast da appunti: {tit_eff}"
                            categoria_memo = analisi_ai.get("categoria") or "Altro"
                            tags_memo = ", ".join(analisi_ai.get("tags", [])) or "appunti, podcast"
                            priorita_memo = int(analisi_ai.get("priorita", 3))
                        except Exception:
                            riassunto_memo = f"Podcast generato da appunti: {tit_eff}"
                            categoria_memo = "Altro"
                            tags_memo = "appunti, podcast"
                            priorita_memo = 3

                        # 3. Inserimento del nuovo memo nel database
                        new_memo_id = database.inserisci_memo(
                            tipo_contenuto="testo",
                            titolo=tit_eff,
                            riassunto=riassunto_memo,
                            testo_originale=testo_effettivo,
                            categoria=categoria_memo,
                            priorita=priorita_memo,
                            tags=tags_memo
                        )

                        # 4. Sintesi audio MP3
                        engine_podcast = "xtts" if voce_scelta.startswith("clone:") else ("edge" if "Neural" in voce_scelta else "kokoro")
                        speed_podcast = float(st.session_state.get("cfg_podcast_speed") or settings.get("podcast_speed", 1.0))

                        res_audio = podcast_tts.genera_audio_podcast(
                            testo_completo=narrazione_completa,
                            titolo=tit_eff,
                            fonte=fonte_eff,
                            id_riferimento=new_memo_id,
                            voce=voce_scelta,
                            velocita=speed_podcast,
                            engine=engine_podcast
                        )

                        if res_audio.get("successo") and os.path.exists(res_audio["percorso_assoluto"]):
                            database.imposta_podcast_memo(
                                memo_id=new_memo_id,
                                audio_path=res_audio["percorso_relativo"],
                                durata=res_audio["durata_secondi"],
                                intro=intro_norm,
                                incluso=1
                            )
                            genera_feed_rss(FEED_PORT)
                            st.success(f"🎉 Podcast '{tit_eff}' generato con successo e aggiunto al feed AntennaPod!")
                            st.rerun()
                        else:
                            st.error(f"Errore generazione audio: {res_audio.get('errore')}")

    # --------------------------------------------------------------------------
    # CONVERSIONE ARTICOLI ESISTENTI NEL DATABASE
    # --------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("🪄 Converti articoli esistenti in Podcast Audio (1-Click)", expanded=False):
        st.caption("Puoi generare all'istante l'episodio podcast per qualsiasi memo dell'archivio contenente un link web:")
        
        # Memo con link che non hanno ancora un podcast
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, titolo, link_originale, categoria, data_creazione 
            FROM memo 
            WHERE link_originale IS NOT NULL AND link_originale != '' 
              AND (audio_podcast_path IS NULL OR audio_podcast_path = '')
              AND cestinato = 0
            ORDER BY data_creazione DESC
            LIMIT 15
        """)
        memo_da_convertire = [dict(r) for r in cursor.fetchall()]
        conn.close()

        if not memo_da_convertire:
            st.info("Tutti gli articoli presenti con link hanno già un episodio podcast generato!")
        else:
            for m in memo_da_convertire:
                col_m1, col_m2 = st.columns([3.5, 1.2], vertical_alignment="center")
                with col_m1:
                    st.write(f"📌 **#{m['id']}** — {m['titolo']} *({m['categoria']})*")
                    st.caption(f"🔗 {m['link_originale'][:80]}...")
                with col_m2:
                    if st.button("🎙️ Genera Podcast", key=f"btn_convert_pod_{m['id']}", use_container_width=True, type="primary"):
                        with st.spinner("Estrazione testo e sintesi vocale in corso..."):
                            art = podcast_scraper.estrai_articolo_pulito(m['link_originale'])
                            if art.get("successo") and len(art.get("testo_pulito", "")) >= 100:
                                intro, completo = podcast_scraper.genera_intro_podcast(art)
                                res_audio = podcast_tts.genera_audio_podcast(
                                    testo_completo=completo,
                                    titolo=m['titolo'],
                                    fonte=art.get("fonte") or m['categoria'],
                                    id_riferimento=m['id'],
                                    voce=settings.get("podcast_voice", "im_nicola"),
                                    velocita=float(settings.get("podcast_speed", 1.0)),
                                    engine=settings.get("podcast_engine", "kokoro")
                                )
                                if res_audio.get("successo"):
                                    database.imposta_podcast_memo(
                                        memo_id=m['id'],
                                        audio_path=res_audio["percorso_relativo"],
                                        durata=res_audio["durata_secondi"],
                                        intro=intro,
                                        incluso=1
                                    )
                                    genera_feed_rss(FEED_PORT)
                                    st.success(f"Episodio per '{m['titolo']}' generato con successo!")
                                    st.rerun()
                                else:
                                    st.error("Errore durante la sintesi vocale.")
                            else:
                                st.error("Impossibile estrarre il testo pulito dal link indicato.")
