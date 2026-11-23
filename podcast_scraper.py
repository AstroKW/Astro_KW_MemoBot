import os
import sys
import re
import urllib.parse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import trafilatura
import ai_service
import web_scraper

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "DNT": "1"
}

MESI_ITALIANI = {
    1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
    5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
    9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
}

GIORNI_ITALIANI = {
    0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì",
    4: "Venerdì", 5: "Sabato", 6: "Domenica"
}

def data_corrente_parlata() -> str:
    """Restituisce la data odierna in italiano parlato naturale (es. Giovedì 5 novembre 2026)."""
    now = datetime.now()
    giorno_sett = GIORNI_ITALIANI.get(now.weekday(), "")
    mese = MESI_ITALIANI.get(now.month, "")
    return f"{giorno_sett} {now.day} {mese} {now.year}".strip()

def ricomponi_testo_pdf(testo: str) -> str:
    """
    Riconnette le righe spezzate tipiche del copia-incolla da file PDF o colonne di testo strette.
    Ricompone le parole sillabate con trattino a fine riga (es. 'imposta-\nzione' -> 'impostazione'),
    unisce le righe non terminate da punteggiatura forte in un unico paragrafo continuo
    e preserva i veri stacchi di paragrafo (doppi a-capo) ed elenchi puntati.
    """
    if not testo:
        return ""

    # 1. Normalizza ritorni a capo Windows/Mac
    t = testo.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Ricostruisci sillabazioni a fine riga con trattino: es. 'imposta-\n zione' -> 'impostazione'
    t = re.sub(r'(\w+)[\-–—]\n\s*(\w+)', r'\1\2', t)

    # 3. Dividi in blocchi separati da doppi ritorni a capo (veri paragrafi)
    blocchi = re.split(r'\n\s*\n+', t)
    blocchi_puliti = []

    for b in blocchi:
        righe = [r.strip() for r in b.split("\n") if r.strip()]
        if not righe:
            continue

        paragrafo_unito = []
        for riga in righe:
            # Se la riga è un punto elenco (*, -, •, 1.), va su nuova riga
            if re.match(r'^[\*\-•]\s+|^\d+[\.\)]\s+', riga):
                if paragrafo_unito:
                    paragrafo_unito.append("\n" + riga)
                else:
                    paragrafo_unito.append(riga)
            else:
                if paragrafo_unito and not paragrafo_unito[-1].endswith("\n"):
                    paragrafo_unito.append(" " + riga)
                else:
                    paragrafo_unito.append(riga)

        blocco_fuso = "".join(paragrafo_unito)
        blocco_fuso = re.sub(r'[ \t]+', ' ', blocco_fuso).strip()
        blocchi_puliti.append(blocco_fuso)

    return "\n\n".join(blocchi_puliti)

def pulisci_testo_per_voce(testo: str) -> str:
    """
    Normalizza simboli, numeri, abbreviazioni e formattazioni per renderli
    fluidi e naturali durante la lettura da parte del sintetizzatore vocale.
    """
    if not testo:
        return ""
    
    # 0. Ricostruisci preventivamente i paragrafi per eliminare a-capo spuri (tipici da PDF o colonne)
    t = ricomponi_testo_pdf(testo)
    
    # Rimuovi URL web espliciti (impossibili da leggere piacevolmente a voce)
    t = re.sub(r'https?://\S+|www\.\S+', '', t)
    
    # Rimuovi link markdown [testo](url) mantenendo solo il testo
    t = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', t)

    # Rimuovi note e citazioni numeriche tra parentesi quadre (es. [1], [1,2], [3-5])
    t = re.sub(r'\[\s*\d+(?:[\s,–\-\.]+\d+)*\s*\]', '', t)
    
    # Rimuovi tag HTML residui o entità
    t = re.sub(r'<[^>]+>', ' ', t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "e").replace("&quot;", '"')
    
    # Simboli monetari
    t = re.sub(r'€\s*(\d+([.,]\d+)?)', r'\1 euro', t)
    t = re.sub(r'(\d+([.,]\d+)?)\s*€', r'\1 euro', t)
    t = t.replace("€", " euro ")
    t = t.replace("$", " dollari ")
    t = t.replace("£", " sterline ")
    
    # Percentuali
    t = re.sub(r'(\d+)%', r'\1 percento', t)
    t = t.replace("%", " percento ")
    
    # Unità di misura frequenti
    t = re.sub(r'\bkm/h\b', 'chilometri orari', t, flags=re.IGNORECASE)
    t = re.sub(r'\bkm\b', 'chilometri', t, flags=re.IGNORECASE)
    t = re.sub(r'\bmin\b', 'minuti', t, flags=re.IGNORECASE)
    t = re.sub(r'\bsec\b', 'secondi', t, flags=re.IGNORECASE)
    t = re.sub(r'\bkg\b', 'chilogrammi', t, flags=re.IGNORECASE)
    
    # Punteggiatura e apici
    t = t.replace("’", "'").replace("“", '"').replace("”", '"').replace("«", '"').replace("»", '"')
    t = re.sub(r'\.{2,}', '...', t)
    t = re.sub(r'[\t\r]+', ' ', t)
    t = re.sub(r' +', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n\n', t)
    
    return t.strip()

def rimuovi_citazioni_scientifiche(testo: str) -> str:
    """
    Rimuove citazioni bibliografiche e note accademiche nel testo:
    - Numeriche tra parentesi quadre: es. [1], [1,2], [1-4], [3, 5, 8]
    - Autore-Anno tra parentesi tonde: es. (UNESCO, 2015; Coffee, 2022), (Cetorelli & Papi, 2024), (Rossi et al., 2020)
    Preserva la fluidità del testo ripulendo spazi e punteggiatura residui.
    """
    if not testo:
        return ""
    t = testo

    # 1. Rimuovi citazioni numeriche tipo [1], [1,2], [1-4], [3, 5, 8]
    t = re.sub(r'\[\s*\d+(?:[\s,–\-\.]+\d+)*\s*\]', '', t)

    # 2. Rimuovi citazioni autore-anno tra parentesi tonde
    cit_pattern = r'\(\s*(?:[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ\s&–\-\./]+(?:\bet al\.?)?,?\s*\d{4}[a-z]?(?:\s*,\s*p(?:p)?\.\s*\d+[\-–\d]*)?(?:;\s*)?)+\s*\)'
    t = re.sub(cit_pattern, '', t)

    # 3. Pulisci spazi prima di punteggiatura e spazi doppi
    t = re.sub(r'\s+([,.:;?!])', r'\1', t)
    t = re.sub(r'[ \t]+', ' ', t)
    return t.strip()

def estrai_testo_da_documento(file_bytes: bytes, filename: str) -> tuple[str, str]:
    """
    Estrae il testo da un file PDF o da un'immagine caricata.
    - Se PDF digitale: estrazione istantanea ad alta fedeltà con PyMuPDF (fitz).
    - Se PDF scansionato o Immagine (.jpg/.png): estrazione tramite modulo Vision OCR.
    Restituisce: (testo_estratto, titolo_suggerito)
    """
    ext = os.path.splitext(filename)[1].lower()
    titolo_suggerito = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()

    if ext == ".pdf":
        try:
            try:
                import fitz
            except ImportError:
                print("[PODCAST_SCRAPER] ⚠️ Avviso: PyMuPDF non installato. Esegui 'pip install pymupdf' per abilitare l'estrazione testo da PDF.")
                return "", titolo_suggerito

            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pagine = [page.get_text() for page in doc]
            testo = "\n\n".join(pagine).strip()

            # Se il PDF ha testo digitale sufficiente
            if len(testo) >= 100:
                return ricomponi_testo_pdf(testo), titolo_suggerito

            # Fallback per PDF scansionati privi di testo vettoriale
            print("[PODCAST_SCRAPER] PDF privo di layer testo vettoriale. Avvio OCR Vision...")
            import vision_processor
            testi_ocr = []
            for i, page in enumerate(doc):
                if i >= 10:
                    break
                pix = page.get_pixmap(dpi=150)
                temp_img = os.path.join(os.path.dirname(__file__), "allegati", f"temp_pdf_ocr_{i}.jpg")
                pix.save(temp_img)
                try:
                    t_ocr = vision_processor.analizza_immagine(temp_img)
                    if t_ocr and "elaborazione ocr non riuscita" not in t_ocr.lower():
                        testi_ocr.append(t_ocr)
                finally:
                    if os.path.exists(temp_img):
                        try:
                            os.remove(temp_img)
                        except Exception:
                            pass

            testo_finale = "\n\n".join(testi_ocr).strip()
            return (ricomponi_testo_pdf(testo_finale) if testo_finale else testo), titolo_suggerito
        except Exception as e:
            print(f"[PODCAST_SCRAPER] Errore estrazione PDF: {e}")
            return "", titolo_suggerito

    elif ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        try:
            import vision_processor
            temp_img = os.path.join(os.path.dirname(__file__), "allegati", f"temp_upload_{filename}")
            with open(temp_img, "wb") as f:
                f.write(file_bytes)
            try:
                testo = vision_processor.analizza_immagine(temp_img)
                if testo and "elaborazione ocr non riuscita" not in testo.lower():
                    return ricomponi_testo_pdf(testo), titolo_suggerito
                return "", titolo_suggerito
            finally:
                if os.path.exists(temp_img):
                    try:
                        os.remove(temp_img)
                    except Exception:
                        pass
        except Exception as e:
            print(f"[PODCAST_SCRAPER] Errore estrazione immagine: {e}")
            return "", titolo_suggerito

    return "", titolo_suggerito

def estrai_articolo_pulito(url: str) -> dict:
    """
    Estrae il testo integrale e i metadati puliti di un articolo web utilizzando
    trafilatura integrata con BeautifulSoup per i meta-tag OpenGraph.
    Include fallback trasparente su browser nativo headless (Chrome / Edge) in caso
    di siti protetti da WAF o anti-bot (Akamai, Cloudflare, ecc.).
    """
    try:
        # 1. Scaricamento HTML con trafilatura (gestisce redirect e codifiche)
        downloaded = trafilatura.fetch_url(url)
        if downloaded and ("<title>Access Denied</title>" in downloaded or "Reference #" in downloaded):
            downloaded = ""

        # 2. Fallback con requests se trafilatura non scarica
        if not downloaded:
            try:
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
                if resp.status_code == 200 and "<title>Access Denied</title>" not in resp.text and "Reference #" not in resp.text:
                    downloaded = resp.text
            except Exception:
                downloaded = ""
            
        # 3. Fallback con browser nativo Chromium headless per siti con protezioni avanzate (es. Fanpage su Akamai)
        if not downloaded or len(downloaded) < 500:
            print(f"[PODCAST_SCRAPER] 🛡️ Pagina protetta da WAF o non scaricabile via HTTP standard. Avvio fallback browser headless per: {url}...")
            downloaded = web_scraper.scarica_html_con_browser(url)

        if not downloaded:
            return {"successo": False, "errore": "Impossibile scaricare la pagina"}

        # Estrazione corpo pulito con trafilatura
        testo_pulito = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_precision=True
        ) or ""

        # Estrazione metadati ausiliari con BeautifulSoup
        soup = BeautifulSoup(downloaded, "html.parser")
        
        # 1. Titolo
        titolo = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            titolo = og_title["content"].strip()
        elif soup.title and soup.title.string:
            titolo = soup.title.string.strip()
            
        # Pulisci eventuale brand name nel titolo (es. "Notizia - Dagospia")
        if " - " in titolo:
            parti = titolo.rsplit(" - ", 1)
            if len(parti[0]) > 15:
                titolo = parti[0].strip()

        # 2. Fonte / Nome del sito
        fonte = ""
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            fonte = og_site["content"].strip()
        else:
            domain = urllib.parse.urlparse(url).netloc
            fonte = domain.replace("www.", "").replace("m.", "").split(".")[0].capitalize()

        # 3. Immagine di copertina
        cover_image = ""
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            cover_image = og_img["content"].strip()

        # 4. Descrizione sommario
        descrizione = ""
        og_desc = soup.find("meta", property="og:description")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if og_desc and og_desc.get("content"):
            descrizione = og_desc["content"].strip()
        elif meta_desc and meta_desc.get("content"):
            descrizione = meta_desc["content"].strip()

        # Se trafilatura ha estratto meno di 150 caratteri, tentiamo un fallback sui tag <p>
        if len(testo_pulito) < 150:
            paragrafi = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 35]
            testo_pulito = "\n\n".join(paragrafi)

        return {
            "successo": bool(testo_pulito),
            "titolo": titolo or "Articolo Web",
            "fonte": fonte or "Web",
            "descrizione": descrizione,
            "testo_pulito": testo_pulito.strip(),
            "cover_image": cover_image,
            "url": url
        }

    except Exception as e:
        print(f"[PODCAST_SCRAPER] Errore estrazione articolo: {e}")
        return {"successo": False, "errore": str(e)}

def rimuovi_titolo_da_inizio_testo(testo: str, titolo: str) -> str:
    """
    Rimuove l'eventuale ripetizione del titolo (o intestazione identica) all'inizio
    del corpo dell'articolo per evitare che il sintetizzatore vocale rilegga
    il titolo subito dopo aver terminato l'introduzione.
    """
    if not testo or not titolo:
        return testo or ""
    t = testo.strip()
    titolo_norm = re.sub(r'[^\w\s]', '', titolo.lower()).strip()
    if len(titolo_norm) < 8:
        return t

    paragrafi = [p for p in t.split('\n') if p.strip()]
    if not paragrafi:
        return t

    primo = paragrafi[0].strip()
    primo_norm = re.sub(r'[^\w\s]', '', primo.lower()).strip()

    # Se il primo paragrafo è esattamente il titolo (o quasi identico, es. Fanpage)
    if primo_norm == titolo_norm or (primo_norm.startswith(titolo_norm) and len(primo_norm) <= len(titolo_norm) + 15):
        return '\n\n'.join(paragrafi[1:]).strip()

    # Se il primo paragrafo inizia con il titolo ed è seguito da un separatore (es. Dagospia: TITOLO – Sommario)
    for sep in [' – ', ' - ', ' — ', ' : ', ' | ']:
        if sep in primo:
            parti = primo.split(sep, 1)
            parte_sx_norm = re.sub(r'[^\w\s]', '', parti[0].lower()).strip()
            if parte_sx_norm == titolo_norm or (len(titolo_norm) >= 20 and parte_sx_norm.startswith(titolo_norm[:20])):
                paragrafi[0] = parti[1].strip()
                return '\n\n'.join(paragrafi).strip()

    # Se il primo paragrafo inizia direttamente col titolo senza separatore esplicito
    if primo_norm.startswith(titolo_norm):
        resto = primo[len(titolo):].strip()
        resto = re.sub(r'^[\s\-–—:\.]+', '', resto).strip()
        if len(resto) > 20:
            paragrafi[0] = resto
            return '\n\n'.join(paragrafi).strip()
        else:
            return '\n\n'.join(paragrafi[1:]).strip()

    return t

def genera_intro_podcast(dati_articolo: dict) -> tuple[str, str]:
    """
    Compone l'intro parlata radiofonica diretta (Data + Fonte + Titolo)
    ed elimina qualsiasi ripetizione dall'inizio dell'articolo, restituendo
    la traccia testuale completa pronta per la lettura TTS naturale e fluida.
    """
    titolo = dati_articolo.get("titolo", "Articolo Web")
    fonte = dati_articolo.get("fonte", "Web")
    testo = dati_articolo.get("testo_pulito", "")
    data_str = data_corrente_parlata()

    # Formula radiofonica snella e diretta (Opzione A): zero ridondanze, zero attese
    intro_parlata = (
        f"Oggi è {data_str}. Da {fonte}: {titolo}. "
        f"Buon ascolto, segue l'articolo completo."
    )

    # 1. Rimuovi l'eventuale titolo duplicato all'inizio del testo estratto
    testo_senza_titolo_iniziale = rimuovi_titolo_da_inizio_testo(testo, titolo)

    # 2. Normalizza testo e intro per la sintesi vocale
    testo_corpo_normalizzato = pulisci_testo_per_voce(testo_senza_titolo_iniziale)
    intro_normalizzata = pulisci_testo_per_voce(intro_parlata)

    testo_narrazione_completo = f"{intro_normalizzata}\n\n{testo_corpo_normalizzato}"

    return intro_normalizzata, testo_narrazione_completo
