import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Modello Vision configurabile da .env (default: qwen2.5vl:7b)
VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:7b")

def analizza_immagine(file_path: str, caption_utente: str = "") -> str:
    """
    Invia l'immagine a un modello Vision locale (es. qwen2.5vl:7b o minicpm-v)
    per estrarre testo (OCR), analizzare schermate, tabelle o scontrini.
    """
    if not os.path.exists(file_path):
        print(f"[VISION] Errore: il file {file_path} non esiste.")
        return caption_utente or "Immagine non trovata."

    print(f"[VISION] Analisi OCR con modello {VISION_MODEL} in corso su: {file_path}...")

    guida_nota = f"L'utente ha allegato questa nota all'immagine: \"{caption_utente}\".\n" if caption_utente else ""

    prompt = f"""{guida_nota}Sei un assistente specializzato in Visione Artificiale e OCR ad alta precisione.
Il tuo compito è:
1. Trascrivere fedelmente ed estrarre TUTTO il testo visibile presente nell'immagine (inclusi cartelli, schermate di smartphone, chat, tabelle, scontrini, codici o documenti).
2. Se l'immagine è uno screenshot di un'applicazione o sito web, descrivi chiaramente la schermata, cosa rappresenta e riporta i dati chiave.
3. Se l'immagine è una foto senza testo, descrivi accuratamente il soggetto e gli elementi principali in italiano.

Fornisci direttamente il testo estratto e le informazioni rilevate, senza convenevoli.
"""

    try:
        import ai_service
        testo_estratto = ai_service.vision_completion(image_path=file_path, prompt=prompt)
        
        if caption_utente:
            testo_completo = f"Nota dell'utente: {caption_utente}\n\nTesto/Contenuto estratto dallo screenshot:\n{testo_estratto}"
        else:
            testo_completo = testo_estratto
            
        print("[VISION] Analisi immagine/OCR completata con successo!")
        return testo_completo

    except Exception as e:
        print(f"[VISION] Errore durante l'elaborazione Vision: {e}")
        # Fallback pulito: se c'era una didascalia dell'utente restituisce quella
        if caption_utente:
            return f"Immagine ricevuta con nota: {caption_utente}"
        return "Immagine ricevuta (elaborazione OCR non riuscita)."

if __name__ == "__main__":
    print(f"Modulo vision_processor caricato. Modello attivo: {VISION_MODEL}")
