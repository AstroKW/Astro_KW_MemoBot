import os
import re
import sys
import shutil
import subprocess
import asyncio
import numpy as np
import soundfile as sf
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, APIC, TDRC

PODCAST_DIR = os.path.join(os.path.dirname(__file__), "podcasts")
os.makedirs(PODCAST_DIR, exist_ok=True)

def _trova_ffmpeg() -> str:
    """Rileva l'eseguibile ffmpeg in PATH, tramite imageio-ffmpeg o nella cartella Scripts di Python."""
    bin_path = shutil.which("ffmpeg")
    if bin_path:
        return bin_path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    conda_scripts = os.path.join(sys.prefix, "Scripts", "ffmpeg.exe")
    if os.path.exists(conda_scripts):
        return conda_scripts
    return "ffmpeg"

FFMPEG_BIN = _trova_ffmpeg()

KOKORO_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "kokoro", "kokoro-v1.0.onnx")
KOKORO_VOICES_PATH = os.path.join(os.path.dirname(__file__), "models", "kokoro", "voices-v1.0.bin")

VOCI_DIR = os.path.join(os.path.dirname(__file__), "voci")
os.makedirs(VOCI_DIR, exist_ok=True)

WORKER_PYTHON = os.path.join(os.path.dirname(__file__), "worker_tts", "venv", "Scripts", "python.exe")
WORKER_SCRIPT = os.path.join(os.path.dirname(__file__), "worker_tts", "synthesize.py")

_KOKORO_INSTANCE = None

def elenca_voci_disponibili() -> dict:
    """
    Restituisce un dizionario con tutte le voci selezionabili:
    - Voci standard locali CPU (Nicola, Sara)
    - Voci clonate da campioni in voci/ (es. clone:alberto_angela.wav)
    - Voci cloud (Diego, Elsa)
    """
    voci = {
        "im_nicola": "Nicola 🇮🇹 (Uomo - Kokoro ONNX CPU)",
        "if_sara": "Sara 🇮🇹 (Donna - Kokoro ONNX CPU)"
    }
    
    # Rilevamento voci clonate in voci/
    if os.path.exists(VOCI_DIR):
        for f in sorted(os.listdir(VOCI_DIR)):
            if f.lower().endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a")) and not f.startswith("."):
                nome_base = os.path.splitext(f)[0]
                etichetta = nome_base.replace("_", " ").title()
                voci[f"clone:{f}"] = f"✨ {etichetta} (Voce Clonata - XTTS GPU)"

    voci["it-IT-DiegoNeural"] = "Diego 🇮🇹 (Edge TTS Cloud)"
    voci["it-IT-ElsaNeural"] = "Elsa 🇮🇹 (Edge TTS Cloud)"
    return voci

def get_kokoro_instance():
    """Caricamento singleton del modello neurale locale Kokoro ONNX."""
    global _KOKORO_INSTANCE
    if _KOKORO_INSTANCE is None:
        if not os.path.exists(KOKORO_MODEL_PATH) or not os.path.exists(KOKORO_VOICES_PATH):
            raise FileNotFoundError(f"Modelli Kokoro non trovati in {KOKORO_MODEL_PATH}")
        from kokoro_onnx import Kokoro
        print(f"[PODCAST_TTS] Caricamento modello locale Kokoro in memoria...")
        _KOKORO_INSTANCE = Kokoro(KOKORO_MODEL_PATH, KOKORO_VOICES_PATH)
    return _KOKORO_INSTANCE

def dividi_testo_in_frammenti(testo: str, max_chars: int = 250) -> list[str]:
    """
    Spezza il testo in frasi e blocchi logici brevi (massimo ~250 caratteri)
    rispettando la punteggiatura (. ! ? \n) per garantire pause naturali e massima fedeltà di Kokoro.
    """
    if not testo:
        return []

    # Separa per paragrafi
    paragrafi = [p.strip() for p in testo.split("\n") if p.strip()]
    frammenti_finali = []

    for p in paragrafi:
        # Separa per frasi usando espressione regolare che mantiene i delimitatori
        frasi = re.split(r'([.?!;:]+\s+)', p)
        
        # Riunisci la punteggiatura alla frase precedente
        frasi_ricostruite = []
        i = 0
        while i < len(frasi):
            f = frasi[i].strip()
            if not f:
                i += 1
                continue
            if i + 1 < len(frasi) and re.match(r'^[.?!;:]+', frasi[i+1]):
                f += frasi[i+1].strip()
                i += 2
            else:
                i += 1
            frasi_ricostruite.append(f)

        # Accorpa frasi brevi fino a max_chars
        blocco_corrente = ""
        for frase in frasi_ricostruite:
            if not blocco_corrente:
                blocco_corrente = frase
            elif len(blocco_corrente) + len(frase) + 1 <= max_chars:
                blocco_corrente += " " + frase
            else:
                frammenti_finali.append(blocco_corrente.strip())
                blocco_corrente = frase
        if blocco_corrente:
            frammenti_finali.append(blocco_corrente.strip())

    return frammenti_finali

def applica_tag_id3(file_mp3: str, titolo: str, fonte: str, cover_path: str = None):
    """Aggiunge metadati ID3 e copertina per Android Auto e AntennaPod."""
    try:
        audio = MP3(file_mp3, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass

        audio.tags.add(TIT2(encoding=3, text=titolo))
        audio.tags.add(TPE1(encoding=3, text=fonte or "Astro_KW MemoBot"))
        audio.tags.add(TALB(encoding=3, text="Astro_KW MemoBot Podcast"))
        audio.tags.add(TCON(encoding=3, text="Podcast"))

        # Copertina incorporata
        copertina = cover_path or os.path.join(os.path.dirname(__file__), "LOGO_TONDO_NERO.png")
        if os.path.exists(copertina):
            mime = "image/png" if copertina.lower().endswith(".png") else "image/jpeg"
            with open(copertina, "rb") as img_file:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime=mime,
                        type=3,  # Cover front
                        desc="Cover",
                        data=img_file.read()
                    )
                )
        audio.save()
    except Exception as e:
        print(f"[PODCAST_TTS] Avviso: impossibile scrivere tag ID3: {e}")

def genera_audio_kokoro(testo: str, file_destinazione_mp3: str, voce: str = "im_nicola", velocita: float = 1.0) -> int:
    """
    Sintetizza l'audio localmente con Kokoro ONNX su CPU, concatena i frammenti
    e converte in formato MP3 ottimizzato tramite ffmpeg. Restituisce la durata in secondi.
    """
    kokoro = get_kokoro_instance()
    frammenti = dividi_testo_in_frammenti(testo, max_chars=220)
    
    if not frammenti:
        raise ValueError("Nessun testo da sintetizzare.")

    print(f"[PODCAST_TTS] Kokoro Locale: sintesi di {len(frammenti)} frammenti con voce '{voce}'...")
    audio_pieces = []
    sample_rate = 24000
    pausa_silenzio = np.zeros(int(sample_rate * 0.35), dtype=np.float32)  # Pausa di 350ms tra i blocchi

    for idx, f in enumerate(frammenti):
        try:
            samples, sr = kokoro.create(f, voice=voce, speed=velocita, lang="it")
            sample_rate = sr
            audio_pieces.append(samples)
            audio_pieces.append(pausa_silenzio)
        except Exception as e:
            print(f"[PODCAST_TTS] Avviso frammento #{idx+1} fallito: {e} -> '{f[:30]}...'")

    if not audio_pieces:
        raise RuntimeError("Kokoro non ha generato alcun audio valido.")

    audio_finale = np.concatenate(audio_pieces)
    temp_wav = file_destinazione_mp3.replace(".mp3", "_temp.wav")
    sf.write(temp_wav, audio_finale, sample_rate)

    # Conversione WAV -> MP3 128k con ffmpeg
    cmd_ffmpeg = [
        FFMPEG_BIN, "-y", "-i", temp_wav,
        "-codec:a", "libmp3lame", "-b:a", "128k",
        "-ar", "44100",
        file_destinazione_mp3
    ]
    subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    if os.path.exists(temp_wav):
        try:
            os.remove(temp_wav)
        except Exception:
            pass

    durata_sec = int(len(audio_finale) / sample_rate)
    return durata_sec

async def _genera_audio_edge_async(testo: str, file_destinazione_mp3: str, voce: str = "it-IT-DiegoNeural", velocita: float = 1.0) -> int:
    import edge_tts
    # Formattazione velocita Edge-TTS es. "+0%", "+15%", "-10%"
    perc_speed = int((velocita - 1.0) * 100)
    rate_str = f"{'+' if perc_speed >= 0 else ''}{perc_speed}%"
    
    communicate = edge_tts.Communicate(testo, voice=voce, rate=rate_str)
    await communicate.save(file_destinazione_mp3)

    try:
        audio = MP3(file_destinazione_mp3)
        return int(audio.info.length)
    except Exception:
        return 60

def genera_audio_xtts_gpu(testo: str, file_destinazione_mp3: str, nome_file_voce: str, velocita: float = 1.0) -> int:
    """
    Invoca il worker isolato XTTS-v2 con accelerazione hardware NVIDIA RTX 5070 Ti,
    sintetizza l'audio con la voce campionata e converte in MP3 tramite ffmpeg.
    """
    if not os.path.exists(WORKER_PYTHON) or not os.path.exists(WORKER_SCRIPT):
        raise FileNotFoundError("Worker XTTS non configurato in worker_tts/")

    speaker_path = os.path.join(VOCI_DIR, nome_file_voce)
    if not os.path.exists(speaker_path):
        raise FileNotFoundError(f"File campione voce non trovato: {speaker_path}")

    temp_wav = file_destinazione_mp3.replace(".mp3", "_xtts_temp.wav")
    temp_txt = file_destinazione_mp3.replace(".mp3", "_text.txt")

    # Scrivi il testo in un file per evitare limiti di lunghezza linea comandi su Windows
    with open(temp_txt, "w", encoding="utf-8") as f:
        f.write(testo)

    cmd = [
        WORKER_PYTHON,
        WORKER_SCRIPT,
        "--text_file", temp_txt,
        "--speaker_wav", speaker_path,
        "--output_wav", temp_wav,
        "--language", "it",
        "--speed", str(velocita)
    ]

    print(f"[PODCAST_TTS] 🚀 Invocazione Worker XTTS-v2 su GPU NVIDIA per la voce '{nome_file_voce}'...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    # Rimuovi file testo temporaneo
    if os.path.exists(temp_txt):
        try:
            os.remove(temp_txt)
        except Exception:
            pass

    if proc.returncode != 0 or not os.path.exists(temp_wav):
        print(f"[PODCAST_TTS] ERRORE Worker XTTS:\n{proc.stderr or proc.stdout}")
        raise RuntimeError("Sintesi vocale XTTS fallita sul worker GPU.")

    # Conversione WAV -> MP3 128k con ffmpeg
    cmd_ffmpeg = [
        FFMPEG_BIN, "-y", "-i", temp_wav,
        "-codec:a", "libmp3lame", "-b:a", "128k",
        "-ar", "44100",
        file_destinazione_mp3
    ]
    subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    if os.path.exists(temp_wav):
        try:
            os.remove(temp_wav)
        except Exception:
            pass

    try:
        audio = MP3(file_destinazione_mp3)
        return int(audio.info.length)
    except Exception:
        return 60

def genera_audio_podcast(testo_completo: str, titolo: str, fonte: str, id_riferimento: int | str, voce: str = "im_nicola", velocita: float = 1.0, engine: str = "kokoro") -> dict:
    """
    Punto di ingresso principale per la sintesi vocale:
    - Crea l'MP3 nella cartella podcasts/
    - Aggiunge tag ID3
    - Restituisce percorso relativo, assoluto e durata in secondi.
    """
    nome_file_pulito = re.sub(r'[^a-zA-Z0-9_-]', '_', f"podcast_{id_riferimento}_{fonte[:15]}").lower() + ".mp3"
    percorso_assoluto = os.path.join(PODCAST_DIR, nome_file_pulito)
    percorso_relativo = os.path.join("podcasts", nome_file_pulito)

    print(f"[PODCAST_TTS] Inizio generazione podcast ({engine} | voce: {voce}): {nome_file_pulito}...")

    durata = 0
    if voce.startswith("clone:"):
        nome_file_voce = voce.split("clone:", 1)[1]
        try:
            durata = genera_audio_xtts_gpu(testo_completo, percorso_assoluto, nome_file_voce, velocita=velocita)
        except Exception as e_xtts:
            voce_fb = "if_sara" if any(k in nome_file_voce.lower() for k in ["femminil", "donna", "sara", "ragazza"]) else "im_nicola"
            print(f"[PODCAST_TTS] ⚠️ Avviso: sintesi XTTS GPU non riuscita ({e_xtts}), tentativo fallback su Kokoro CPU (voce: {voce_fb})...")
            try:
                durata = genera_audio_kokoro(testo_completo, percorso_assoluto, voce=voce_fb, velocita=velocita)
            except Exception as e_koko:
                voce_edge = "it-IT-ElsaNeural" if voce_fb == "if_sara" else "it-IT-DiegoNeural"
                print(f"[PODCAST_TTS] ⚠️ Avviso: anche Kokoro locale fallito ({e_koko}), fallback su Edge-TTS Cloud ({voce_edge})...")
                durata = asyncio.run(_genera_audio_edge_async(testo_completo, percorso_assoluto, voce=voce_edge, velocita=velocita))
    elif engine.lower() == "kokoro":
        # Voce default se non specificata o incompatibile
        voce_kokoro = voce if voce in ["im_nicola", "if_sara"] else "im_nicola"
        try:
            durata = genera_audio_kokoro(testo_completo, percorso_assoluto, voce=voce_kokoro, velocita=velocita)
        except Exception as e_koko:
            voce_edge = "it-IT-ElsaNeural" if voce_kokoro == "if_sara" else "it-IT-DiegoNeural"
            print(f"[PODCAST_TTS] ⚠️ Avviso: Kokoro locale non disponibile ({e_koko}), fallback su Edge-TTS Cloud ({voce_edge})...")
            durata = asyncio.run(_genera_audio_edge_async(testo_completo, percorso_assoluto, voce=voce_edge, velocita=velocita))
    else:
        # Edge-TTS
        voce_edge = voce if "it-IT" in voce else "it-IT-DiegoNeural"
        durata = asyncio.run(_genera_audio_edge_async(testo_completo, percorso_assoluto, voce=voce_edge, velocita=velocita))

    applica_tag_id3(percorso_assoluto, titolo=titolo, fonte=fonte)

    dimensione_bytes = os.path.getsize(percorso_assoluto) if os.path.exists(percorso_assoluto) else 0

    print(f"[PODCAST_TTS] ✅ Podcast generato con successo! Durata: {durata}s | Dimensione: {dimensione_bytes // 1024} KB")

    return {
        "successo": True,
        "percorso_assoluto": percorso_assoluto,
        "percorso_relativo": percorso_relativo,
        "nome_file": nome_file_pulito,
        "durata_secondi": durata,
        "dimensione_bytes": dimensione_bytes
    }

