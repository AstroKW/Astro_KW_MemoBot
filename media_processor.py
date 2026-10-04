import os
import sys

# Bypassa il conflitto OpenMP su Windows/Anaconda
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Assicura che ffmpeg.exe (nella cartella Scripts di Anaconda) sia sempre visibile a Whisper
scripts_dir = os.path.join(sys.prefix, 'Scripts')
if scripts_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = scripts_dir + os.pathsep + os.environ.get("PATH", "")

import whisper

_MODEL_WHISPER = None

def get_whisper_model():
    """Caricamento pigro (lazy) del modello Whisper solo quando necessario."""
    global _MODEL_WHISPER
    if _MODEL_WHISPER is None:
        print("Caricamento modello Whisper ('base') in memoria...")
        _MODEL_WHISPER = whisper.load_model("base")
    return _MODEL_WHISPER

def trascrivi_media(file_path):
    """
    Riceve il percorso di un file audio o video e restituisce il testo trascritto.
    Utilizza ffmpeg per decodificare il container audio (.ogg/.mp4).
    """
    if not os.path.exists(file_path):
        print(f"[MEDIA] Errore: Il file {file_path} non esiste.")
        return None

    try:
        print(f"[MEDIA] Trascrizione audio con Whisper in corso: {file_path}...")
        model = get_whisper_model()
        prompt_contesto = (
            "Trascrizione in italiano di un appunto, nota vocale o promemoria personale. "
            "Riunione di lavoro, appuntamento, incontro, scadenze, orari. "
            "Lunedì, martedì, mercoledì, giovedì, venerdì, sabato, domenica. "
            "Ore nove, ore dieci, ore undici, ore dodici, ore quindici, ore diciotto, ore venti."
        )
        result = model.transcribe(
            file_path, 
            fp16=False, 
            language="it",
            initial_prompt=prompt_contesto
        )
        testo = result.get("text", "").strip()
        
        if not testo:
            print("[MEDIA] Trascrizione completata: nessun parlato udibile rilevato.")
            return "Nessun parlato chiaramente udibile nel file multimediale."
            
        return testo

    except Exception as e:
        print(f"[MEDIA] Errore durante la trascrizione con Whisper: {e}")
        return None

if __name__ == "__main__":
    print("Modulo Whisper verificato e pronto all'uso con supporto ffmpeg!")