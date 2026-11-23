import os
import sys
import argparse
import time

# Accettazione automatica della licenza CPML di Coqui XTTS-v2
os.environ["COQUI_TOS_AGREED"] = "1"

def main():
    parser = argparse.ArgumentParser(description="Worker Zero-Shot Voice Cloning con XTTS-v2 su GPU NVIDIA")
    parser.add_argument("--text", type=str, default="", help="Testo da sintetizzare")
    parser.add_argument("--text_file", type=str, default="", help="Percorso di un file di testo contenente l'articolo")
    parser.add_argument("--speaker_wav", type=str, required=True, help="Percorso del file audio campione per la voce")
    parser.add_argument("--output_wav", type=str, required=True, help="Percorso di destinazione del file WAV generato")
    parser.add_argument("--language", type=str, default="it", help="Codice lingua (default: it)")
    parser.add_argument("--speed", type=float, default=1.0, help="Velocità di riproduzione (default: 1.0)")
    
    args = parser.parse_args()

    # Lettura del testo
    testo = args.text
    if args.text_file and os.path.exists(args.text_file):
        with open(args.text_file, "r", encoding="utf-8") as f:
            testo = f.read()

    testo = testo.strip()
    if not testo:
        print("[WORKER_XTTS] ERRORE: Nessun testo fornito per la sintesi.")
        sys.exit(1)

    if not os.path.exists(args.speaker_wav):
        print(f"[WORKER_XTTS] ERRORE: File campione voce non trovato: {args.speaker_wav}")
        sys.exit(1)

    print(f"[WORKER_XTTS] Avvio sintetizzatore su GPU NVIDIA...")
    print(f"[WORKER_XTTS] Voce campione: {os.path.basename(args.speaker_wav)}")
    print(f"[WORKER_XTTS] Lunghezza testo: {len(testo)} caratteri | Lingua: {args.language}")

    start_time = time.time()

    import torch
    import soundfile as sf
    import torchaudio

    # Patch per torchaudio: usa soundfile come backend diretto, evitando dipendenze esterne
    def _sf_load(uri, frame_offset=0, num_frames=-1, normalize=True, channels_first=True, **kwargs):
        data, sample_rate = sf.read(uri, dtype='float32', start=frame_offset, frames=num_frames if num_frames > 0 else -1)
        tensor = torch.from_numpy(data)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)
        elif channels_first and tensor.shape[0] != 1 and tensor.shape[1] == 1:
            tensor = tensor.t()
        return tensor, sample_rate

    def _sf_save(uri, src, sample_rate, channels_first=True, **kwargs):
        arr = src.detach().cpu().numpy()
        if arr.ndim > 1:
            arr = arr.squeeze()
        sf.write(uri, arr, sample_rate)

    torchaudio.load = _sf_load
    torchaudio.save = _sf_save

    from TTS.api import TTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[WORKER_XTTS] Caricamento modello XTTS-v2 su dispositivo: {device} ({torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU'})...")
    
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    # Assicura che la directory di destinazione esista
    os.makedirs(os.path.dirname(os.path.abspath(args.output_wav)), exist_ok=True)

    print(f"[WORKER_XTTS] Sintesi neurale in corso su GPU...")
    tts.tts_to_file(
        text=testo,
        speaker_wav=args.speaker_wav,
        language=args.language,
        file_path=args.output_wav,
        speed=args.speed,
        split_sentences=True
    )

    elapsed = round(time.time() - start_time, 2)
    print(f"[WORKER_XTTS] ✅ Sintesi completata con successo in {elapsed}s!")
    print(f"[WORKER_XTTS] File generato: {args.output_wav}")

if __name__ == "__main__":
    main()
