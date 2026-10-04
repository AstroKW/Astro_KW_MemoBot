import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

# User-Agent realistico per evitare blocchi 403 dai quotidiani/siti web
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "DNT": "1"
}

TIMEOUT_SECONDS = 7

def _pulisci_testo(testo: str) -> str:
    """Rimuove spazi multipli e ritorni a capo ridondanti."""
    if not testo:
        return ""
    return re.sub(r'\s+', ' ', testo).strip()

def estrai_info_youtube(url: str) -> dict:
    """Utilizza l'endpoint ufficiale oEmbed pubblico di YouTube (veloce e affidabile)."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
        resp = requests.get(oembed_url, timeout=TIMEOUT_SECONDS)
        if resp.status_code == 200:
            data = resp.json()
            titolo = data.get("title", "")
            autore = data.get("author_name", "")
            return {
                "titolo": titolo,
                "descrizione": f"Video YouTube di {autore}" if autore else "Video YouTube",
                "testo_articolo": f"Titolo video: {titolo}\nCanale: {autore}\nURL: {url}",
                "fonte": "YouTube",
                "successo": True
            }
    except Exception as e:
        print(f"[SCRAPER] Errore YouTube oEmbed: {e}")
    return None

def estrai_info_instagram(url: str, testo_utente: str = "") -> dict:
    """
    Tenta di estrarre metadati da Instagram (post/reel).
    Gestisce elegantemente la tipica protezione di login di Meta.
    """
    tipo_media = "Reel" if "/reel/" in url.lower() else "Post"
    
    # Header specifici simili a bot di condivisione social
    insta_headers = {
        "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"
    }
    
    try:
        resp = requests.get(url, headers=insta_headers, timeout=TIMEOUT_SECONDS)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Cerca meta tag OpenGraph
            og_title = soup.find("meta", property="og:title")
            og_desc = soup.find("meta", property="og:description")
            
            titolo_raw = og_title["content"] if (og_title and og_title.get("content")) else ""
            desc_raw = og_desc["content"] if (og_desc and og_desc.get("content")) else ""
            
            # Se Instagram restituisce la tipica didascalia con commenti/likes
            didascalia = desc_raw or titolo_raw
            if didascalia and "Instagram" not in didascalia:
                return {
                    "titolo": f"Instagram {tipo_media}: {_pulisci_testo(titolo_raw)[:60]}",
                    "descrizione": _pulisci_testo(desc_raw)[:300],
                    "testo_articolo": _pulisci_testo(didascalia),
                    "fonte": "Instagram",
                    "successo": True
                }
    except Exception as e:
        print(f"[SCRAPER] Errore estrazione Instagram: {e}")

    # Fallback sicuro per Instagram se c'è login wall
    return {
        "titolo": f"Video/Post Instagram ({tipo_media})",
        "descrizione": "Contenuto Instagram (accesso limitato)",
        "testo_articolo": f"Contenuto multimediale da Instagram ({tipo_media}).\nLink: {url}\nNota dell'utente: {testo_utente}",
        "fonte": "Instagram",
        "successo": True
    }

def estrai_articolo_generico(url: str) -> dict:
    """Estrae titolo, meta-descrizione e paragrafi dell'articolo da qualsiasi sito web."""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SECONDS)
        
        # Gestione pagine non trovate o errori HTTP
        if resp.status_code == 404:
            return {
                "titolo": "Pagina non trovata (Errore 404)",
                "descrizione": "Il link inviato non corrisponde a una pagina attiva o è scaduto.",
                "testo_articolo": f"Attenzione: la pagina web {url} ha restituito un codice 404 (non trovata).",
                "fonte": "Web",
                "successo": False
            }
        
        resp.raise_for_status()
        
        # Parsing con BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 1. Rimuovi elementi non testuali / rumorosi
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"]):
            tag.decompose()
            
        # 2. Estrazione Titolo
        titolo = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            titolo = og_title["content"]
        elif soup.title and soup.title.string:
            titolo = soup.title.string
        titolo = _pulisci_testo(titolo)
        
        # 3. Estrazione Descrizione / Sommario
        descrizione = ""
        og_desc = soup.find("meta", property="og:description")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if og_desc and og_desc.get("content"):
            descrizione = og_desc["content"]
        elif meta_desc and meta_desc.get("content"):
            descrizione = meta_desc["content"]
        descrizione = _pulisci_testo(descrizione)
        
        # 4. Estrazione Nome Sito
        og_site = soup.find("meta", property="og:site_name")
        fonte = _pulisci_testo(og_site["content"]) if (og_site and og_site.get("content")) else urllib.parse.urlparse(url).netloc
        
        # 5. Estrazione Corpo Articolo (paragrafi significativi)
        # Priorità a tag semantici <article> o <main>
        container = soup.find("article") or soup.find("main") or soup
        paragrafi = []
        for p in container.find_all("p"):
            testo_p = _pulisci_testo(p.get_text())
            # Filtra frasi brevissime tipiche di bottoni o disclaimer
            if len(testo_p) > 35:
                paragrafi.append(testo_p)
                
        # Unisci i paragrafi fino a un massimo di circa 2500 caratteri per non sovraccaricare l'LLM
        testo_corpo = "\n\n".join(paragrafi)
        if len(testo_corpo) > 2500:
            testo_corpo = testo_corpo[:2500] + "..."
            
        testo_totale = ""
        if descrizione:
            testo_totale += f"Sommario: {descrizione}\n\n"
        testo_totale += f"Contenuto articolo:\n{testo_corpo}" if testo_corpo else descrizione
        
        return {
            "titolo": titolo or "Articolo Web",
            "descrizione": descrizione,
            "testo_articolo": testo_totale.strip(),
            "fonte": fonte,
            "successo": bool(titolo or testo_corpo)
        }
        
    except requests.exceptions.Timeout:
        print(f"[SCRAPER] Timeout durante il caricamento di {url}")
        return {
            "titolo": "Articolo Web (Timeout caricamento)",
            "descrizione": "",
            "testo_articolo": f"Link: {url}\nImpossibile recuperare il contenuto entro {TIMEOUT_SECONDS} secondi.",
            "fonte": urllib.parse.urlparse(url).netloc,
            "successo": False
        }
    except Exception as e:
        print(f"[SCRAPER] Errore estrazione link generico: {e}")
        return {
            "titolo": "Articolo Web",
            "descrizione": "",
            "testo_articolo": f"Link: {url}",
            "fonte": urllib.parse.urlparse(url).netloc,
            "successo": False
        }

def analizza_link_completo(url: str, testo_utente: str = "") -> dict:
    """
    Punto di ingresso principale per l'analisi intelligente di qualsiasi URL.
    Instrada automaticamente verso handler dedicati (YouTube, Instagram) o generico.
    """
    url_lower = url.lower()
    
    # 1. YouTube
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        info = estrai_info_youtube(url)
        if info:
            return info
            
    # 2. Instagram
    if "instagram.com" in url_lower:
        return estrai_info_instagram(url, testo_utente)
        
    # 3. Tutti gli altri articoli e pagine web
    return estrai_articolo_generico(url)

def prepara_prompt_per_ai(url: str, testo_utente: str = "") -> tuple[str, str]:
    """
    Raccoglie il contenuto della pagina e restituisce:
    - testo_per_ai: prompt dettagliato e arricchito con i dati reali del web
    - titolo_suggerito: eventuale titolo già rilevato dalla pagina
    """
    info = analizza_link_completo(url, testo_utente)
    
    parti = [
        f"FONTE: {info.get('fonte', 'Web')}",
        f"LINK ORIGINALE: {url}",
    ]
    if info.get("titolo"):
        parti.append(f"TITOLO DELLA PAGINA/POST: {info['titolo']}")
    if info.get("testo_articolo"):
        parti.append(f"TESTO REALE DEL CONTENUTO ESTRATTO DALLA PAGINA:\n{info['testo_articolo']}")
    if testo_utente:
        parti.append(f"COMMENTO / MESSAGGIO INVIATO DALL'UTENTE INSIEME AL LINK:\n{testo_utente}")
        
    testo_per_ai = "\n\n".join(parti)
    titolo_suggerito = info.get("titolo", "")
    return testo_per_ai, titolo_suggerito

if __name__ == "__main__":
    print("Test modulo web_scraper...")
    # Test su Tomshw
    test_url = "https://www.tomshw.it/hardware/200eur-in-meno-sul-dell-tower-plus-rtx-5070-per-chi-crea-sul-serio"
    risultato = analizza_link_completo(test_url)
    print("\n--- RISULTATO TEST TOMSHW ---")
    print("Titolo:", risultato["titolo"])
    print("Fonte :", risultato["fonte"])
    print("Snippet testo:\n", risultato["testo_articolo"][:250])
