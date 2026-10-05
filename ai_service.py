import os
import base64
import mimetypes
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# CONFIGURAZIONE DEI PROVIDER AI (LOCALE & CLOUD)
# ==============================================================================
# Providers supportati: 'ollama', 'gemini', 'groq', 'openai', 'openrouter', 'custom'
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").strip().lower()

PROVIDER_INFO = {
    "ollama": {
        "nome": "Ollama (Locale)",
        "tipo": "locale",
        "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:14b"),
        "default_vision": os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:7b"),
        "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434")
    },
    "gemini": {
        "nome": "Google Gemini (Cloud Gratuito/Pro)",
        "tipo": "cloud",
        "default_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "default_vision": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY"
    },
    "groq": {
        "nome": "Groq (Cloud Ultra-Veloce)",
        "tipo": "cloud",
        "default_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "default_vision": os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview"),
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY"
    },
    "openai": {
        "nome": "OpenAI ChatGPT (Cloud)",
        "tipo": "cloud",
        "default_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "default_vision": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "base_url": None,
        "api_key_env": "OPENAI_API_KEY"
    },
    "openrouter": {
        "nome": "OpenRouter (Tutti i Modelli Cloud)",
        "tipo": "cloud",
        "default_model": os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct"),
        "default_vision": os.getenv("OPENROUTER_VISION_MODEL", "meta-llama/llama-3.2-11b-vision-instruct"),
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY"
    },
    "custom": {
        "nome": "OpenAI-Compatible Personalizzato",
        "tipo": "custom",
        "default_model": os.getenv("CUSTOM_OPENAI_MODEL", "default"),
        "default_vision": os.getenv("CUSTOM_OPENAI_MODEL", "default"),
        "base_url": os.getenv("CUSTOM_OPENAI_BASE_URL", ""),
        "api_key_env": "CUSTOM_OPENAI_API_KEY"
    }
}

def get_provider() -> str:
    """Restituisce il provider AI attualmente attivo."""
    load_dotenv(override=True)
    p = os.getenv("AI_PROVIDER", "ollama").strip().lower()
    return p if p in PROVIDER_INFO else "ollama"

def get_active_model(for_vision: bool = False) -> str:
    """Restituisce il nome del modello attivo per testo o vision."""
    provider = get_provider()
    info = PROVIDER_INFO[provider]
    if for_vision:
        return info["default_vision"]
    return info["default_model"]

def get_active_provider_label() -> str:
    """Restituisce un'etichetta leggibile per l'interfaccia utente (es. '🏠 Ollama Locale (qwen2.5:14b)')."""
    provider = get_provider()
    info = PROVIDER_INFO[provider]
    modello = get_active_model()
    icona = "🏠" if info["tipo"] == "locale" else "☁️"
    return f"{icona} {info['nome']} ({modello})"

def encode_image_base64(image_path: str) -> tuple[str, str]:
    """Codifica un file immagine in base64 e individua il mime-type corretto."""
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return b64, mime_type

def get_openai_client():
    """Crea e restituisce il client OpenAI configurato per il provider cloud attivo."""
    from openai import OpenAI
    provider = get_provider()
    info = PROVIDER_INFO[provider]
    api_key_name = info.get("api_key_env", "")
    api_key = os.getenv(api_key_name, "") if api_key_name else "none"
    base_url = info.get("base_url")

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    # Headers addizionali per OpenRouter
    if provider == "openrouter":
        kwargs["default_headers"] = {
            "HTTP-Referer": "https://github.com/Astro_KW/MemoBot",
            "X-Title": "Astro_KW MemoBot"
        }

    return OpenAI(**kwargs)

# ==============================================================================
# CHAT COMPLETION UNIFICATA (ANALISI TESTO E RADAR)
# ==============================================================================
def chat_completion(messages: list[dict], format_json: bool = False, temperature: float = 0.2) -> str:
    """
    Esegue una richiesta di chat completion su Ollama o sul provider Cloud attivo.
    Restituisce la stringa di testo della risposta.
    """
    provider = get_provider()
    modello = get_active_model()

    if provider == "ollama":
        import ollama
        kwargs = {
            "model": modello,
            "messages": messages,
            "options": {"temperature": temperature}
        }
        if format_json:
            kwargs["format"] = "json"
        res = ollama.chat(**kwargs)
        return res["message"]["content"]
    else:
        client = get_openai_client()
        kwargs = {
            "model": modello,
            "messages": messages,
            "temperature": temperature
        }
        if format_json:
            kwargs["response_format"] = {"type": "json_object"}
        res = client.chat.completions.create(**kwargs)
        return res.choices[0].message.content

def stream_chat_completion(messages: list[dict], temperature: float = 0.3):
    """
    Esegue una richiesta in streaming (generatore di token) su Ollama o provider Cloud.
    Usato da Astro_KW Radar per mostrare le risposte in tempo reale.
    """
    provider = get_provider()
    modello = get_active_model()

    if provider == "ollama":
        import ollama
        stream = ollama.chat(
            model=modello,
            messages=messages,
            stream=True,
            options={"temperature": temperature}
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
    else:
        client = get_openai_client()
        stream = client.chat.completions.create(
            model=modello,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content

# ==============================================================================
# VISION COMPLETION UNIFICATA (FOTO, SCONTRINI, OCR)
# ==============================================================================
def vision_completion(image_path: str, prompt: str) -> str:
    """
    Invia un'immagine con relativo prompt al modello Vision locale o Cloud.
    Restituisce il testo estratto o l'analisi visiva.
    """
    provider = get_provider()
    modello_vision = get_active_model(for_vision=True)

    if provider == "ollama":
        import ollama
        res = ollama.chat(
            model=modello_vision,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [image_path]
            }]
        )
        return res["message"]["content"].strip()
    else:
        client = get_openai_client()
        b64_img, mime = encode_image_base64(image_path)
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{b64_img}"
                    }
                }
            ]
        }]
        res = client.chat.completions.create(
            model=modello_vision,
            messages=messages,
            temperature=0.2
        )
        return res.choices[0].message.content.strip()

# ==============================================================================
# AUDIO TRANSCRIPTION UNIFICATA (WHISPER LOCALE O CLOUD)
# ==============================================================================
def audio_transcription(file_path: str) -> str | None:
    """
    Trascrive un file audio.
    Se il provider è Groq o OpenAI (e hanno API key configurata), usa le loro API Whisper ultra-veloci.
    Altrimenti usa il motore Whisper locale con ffmpeg.
    """
    provider = get_provider()
    
    # 1. Se l'utente usa Groq e ha la chiave, usa Whisper Cloud di Groq (fulmineo, <1 secondo)
    if provider == "groq" and os.getenv("GROQ_API_KEY"):
        try:
            print("[AUDIO] Trascrizione vocale con Groq Whisper Cloud in corso...")
            from openai import OpenAI
            client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
            with open(file_path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=f,
                    language="it"
                )
            testo = transcription.text.strip()
            print("[AUDIO] Trascrizione Groq completata con successo!")
            return testo if testo else "Nessun parlato chiaramente udibile nel file multimediale."
        except Exception as e:
            print(f"[AUDIO] Errore trascrizione Groq: {e}. Ripiego su Whisper locale...")

    # 2. Se l'utente usa OpenAI e ha la chiave, usa Whisper Cloud ufficiale di OpenAI
    elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            print("[AUDIO] Trascrizione vocale con OpenAI Whisper Cloud in corso...")
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            with open(file_path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="it"
                )
            testo = transcription.text.strip()
            print("[AUDIO] Trascrizione OpenAI completata con successo!")
            return testo if testo else "Nessun parlato chiaramente udibile nel file multimediale."
        except Exception as e:
            print(f"[AUDIO] Errore trascrizione OpenAI: {e}. Ripiego su Whisper locale...")

    # 3. Fallback standard: Whisper locale (con ffmpeg)
    import media_processor
    return media_processor.trascrivi_media_locale(file_path)

# ==============================================================================
# DIAGNOSTICA E GESTIONE CONFIGURAZIONE (.ENV)
# ==============================================================================
def test_connessione_ai() -> tuple[bool, str, float]:
    """
    Esegue un test rapido del provider AI attualmente attivo.
    Restituisce (successo: bool, messaggio: str, tempo_secondi: float).
    """
    import time
    provider = get_provider()
    label = get_active_provider_label()
    
    t0 = time.time()
    try:
        messaggio_test = [{"role": "user", "content": "Rispondi esclusivamente con la parola 'OK'."}]
        risposta = chat_completion(messaggio_test, temperature=0.1)
        elapsed = round(time.time() - t0, 2)
        if "ok" in risposta.lower():
            return True, f"Connessione a {label} completata con successo in {elapsed}s!", elapsed
        else:
            return True, f"Connessione a {label} riuscita in {elapsed}s (Risposta: {risposta[:50]}...)", elapsed
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        return False, f"Errore di connessione a {label}: {e}", elapsed

def salva_configurazione_env(aggiornamenti: dict) -> bool:
    """
    Aggiorna in modo sicuro le variabili nel file .env mantenendo intatte le altre righe.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    righe = []
    chiavi_trovate = set()
    
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for linea in f:
                linea_strip = linea.strip()
                if linea_strip and not linea_strip.startswith("#") and "=" in linea_strip:
                    k, v = linea_strip.split("=", 1)
                    k = k.strip()
                    if k in aggiornamenti:
                        righe.append(f"{k}={aggiornamenti[k]}\n")
                        chiavi_trovate.add(k)
                        continue
                righe.append(linea)
    
    # Aggiungi le chiavi nuove non ancora presenti
    for k, v in aggiornamenti.items():
        if k not in chiavi_trovate:
            righe.append(f"{k}={v}\n")
            
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(righe)
        load_dotenv(env_path, override=True)
        return True
    except Exception as e:
        print(f"[AI_SERVICE] Errore salvataggio .env: {e}")
        return False
