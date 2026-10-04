import os
import sys
import re
import asyncio

# Forza la codifica UTF-8 su console Windows per evitare errori di encoding con caratteri speciali ed emoji
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from dotenv import load_dotenv
from telegram import Bot
import database
import ai_processor
import media_processor
import web_scraper
import vision_processor

# Carica configurazione da .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "")
ALLOWED_USER_IDS = set()
for uid in ALLOWED_USER_IDS_RAW.split(","):
    uid_clean = uid.strip()
    if uid_clean.isdigit():
        ALLOWED_USER_IDS.add(int(uid_clean))

# Cartella temporanea per scaricare audio/video/foto da Telegram
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Regex per identificare URL ovunque nel testo
URL_REGEX = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+', re.IGNORECASE)

async def estrai_dati_messaggio(msg, bot):
    """
    Scarica eventuali media e ricava il testo, link e tipo da un singolo messaggio Telegram.
    Restituisce un dizionario coi dettagli e il percorso temporaneo del file scaricato.
    """
    tipo_contenuto = "testo"
    testo_originale = ""
    link_originale = ""
    percorso_file = None

    testo_ricevuto = msg.text or msg.caption or ""
    trovati_link = URL_REGEX.findall(testo_ricevuto)
    if trovati_link:
        link_originale = trovati_link[0]
        if not link_originale.lower().startswith("http"):
            link_originale = "https://" + link_originale

    # 1. TESTO
    if msg.text:
        testo_originale = msg.text
        if link_originale:
            tipo_contenuto = "link"

    # 2. FOTO / SCREENSHOT (con OCR)
    elif msg.photo:
        tipo_contenuto = "immagine"
        file_obj = msg.photo[-1]
        telegram_file = await bot.get_file(file_obj.file_id)
        percorso_file = os.path.join(DOWNLOAD_DIR, f"foto_{msg.message_id}.jpg")
        await telegram_file.download_to_drive(percorso_file)
        
        print(f"Scansione OCR screenshot/foto #{msg.message_id}...")
        testo_originale = vision_processor.analizza_immagine(percorso_file, caption_utente=msg.caption)
        if link_originale:
            tipo_contenuto = "link"

    # 3. AUDIO / VOCALE (Whisper)
    elif msg.voice or msg.audio:
        tipo_contenuto = "audio"
        file_obj = msg.voice or msg.audio
        telegram_file = await bot.get_file(file_obj.file_id)
        percorso_file = os.path.join(DOWNLOAD_DIR, f"audio_{msg.message_id}.ogg")
        await telegram_file.download_to_drive(percorso_file)
        
        print(f"Trascrizione audio #{msg.message_id}...")
        trascritto = media_processor.trascrivi_media(percorso_file) or "Audio non trascrivibile"
        if msg.caption:
            testo_originale = f"Didascalia: {msg.caption}\nTrascrizione: {trascritto}"
        else:
            testo_originale = trascritto

    # 4. VIDEO (Whisper)
    elif msg.video or msg.video_note:
        tipo_contenuto = "video"
        file_obj = msg.video or msg.video_note
        telegram_file = await bot.get_file(file_obj.file_id)
        percorso_file = os.path.join(DOWNLOAD_DIR, f"video_{msg.message_id}.mp4")
        await telegram_file.download_to_drive(percorso_file)

        print(f"Trascrizione video #{msg.message_id}...")
        trascritto = media_processor.trascrivi_media(percorso_file) or "Video non trascrivibile"
        if msg.caption:
            testo_originale = f"Didascalia: {msg.caption}\nTrascrizione: {trascritto}"
        else:
            testo_originale = trascritto

    from datetime import datetime
    data_locale = msg.date.astimezone().strftime("%Y-%m-%d %H:%M:%S") if msg.date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "msg_id": msg.message_id,
        "reply_to_id": msg.reply_to_message.message_id if msg.reply_to_message else None,
        "tipo_contenuto": tipo_contenuto,
        "testo_originale": testo_originale.strip(),
        "link_originale": link_originale,
        "percorso_file": percorso_file,
        "data_creazione": data_locale
    }

async def scarica_e_elabora():
    """Scarica i messaggi accumulati, gestisce risposte collegate (Reply-To) e aggiorna il DB."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "il_tuo_token_qui":
        print("[ERRORE] TELEGRAM_BOT_TOKEN non configurato nel file .env!")
        print("         Compila il file .env inserendo il token del tuo bot Telegram.")
        return

    # Inizializza o aggiorna schema DB
    database.init_db()

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    print("Connessione a Telegram in corso...")

    if ALLOWED_USER_IDS:
        print(f"[WHITELIST ATTIVA] ID autorizzati: {sorted(list(ALLOWED_USER_IDS))}")
    else:
        print("[AVVISO SICUREZZA] Whitelist DISATTIVATA (nessun ID in ALLOWED_TELEGRAM_USER_IDS).")
        print("                   I messaggi saranno accettati. Ti mostreremo l'ID mittente per aiutarti a configurare .env")

    updates = await bot.get_updates()

    if not updates:
        print("Nessun nuovo messaggio da elaborare su Telegram.")
        return

    print(f"Trovati {len(updates)} nuovi aggiornamenti. Inizio elaborazione batch...\n")

    max_update_id = 0
    messaggi_grezzi = []

    # 1. Filtraggio e download iniziale
    for update in updates:
        if update.update_id > max_update_id:
            max_update_id = update.update_id

        if not update.message:
            continue

        msg = update.message
        user = msg.from_user
        user_id = user.id if user else None
        username = (user.username or user.first_name) if user else "Sconosciuto"

        # Controllo Whitelist
        if ALLOWED_USER_IDS:
            if user_id not in ALLOWED_USER_IDS:
                print(f"[BLOCCATO] Messaggio #{msg.message_id} ignorato da utente non autorizzato: ID={user_id} (@{username})")
                continue
        else:
            print(f"[INFO MITTENTE] Ricevuto memo da: ID={user_id} (@{username})")

        dati = await estrai_dati_messaggio(msg, bot)
        if dati["testo_originale"]:
            messaggi_grezzi.append(dati)

    # 2. Risoluzione della catena "Rispondi" (Reply-To Aggregation)
    # Dizionario dei memo radice del batch corrente: {msg_id: memo_data}
    cluster_batch = {}
    memo_ordinati = sorted(messaggi_grezzi, key=lambda x: x["msg_id"])

    for item in memo_ordinati:
        reply_to_id = item["reply_to_id"]

        # Caso A: È una risposta a un messaggio presente NELLO STESSO BATCH
        if reply_to_id and reply_to_id in cluster_batch:
            padre = cluster_batch[reply_to_id]
            print(f"🔗 [COLLEGAMENTO RISPONDI] Il messaggio #{item['msg_id']} è collegato al messaggio radice #{reply_to_id}!")
            
            # Unisci il testo
            padre["testo_originale"] += f"\n\n[Integrazione/Risposta]: {item['testo_originale']}"
            
            # Se il figlio contiene un link e il padre no, memorizza il link
            if not padre["link_originale"] and item["link_originale"]:
                padre["link_originale"] = item["link_originale"]
                padre["tipo_contenuto"] = "link"

            # Rimuovi file temporanei del messaggio integrato
            if item["percorso_file"] and os.path.exists(item["percorso_file"]):
                try:
                    os.remove(item["percorso_file"])
                except Exception:
                    pass
            continue

        # Caso B: È una risposta a un memo già archiviato nel DATABASE in precedenza
        if reply_to_id:
            memo_db = database.trova_memo_per_telegram_id(reply_to_id)
            if memo_db:
                print(f"🔄 [AGGIORNAMENTO MEMO ESISTENTE] Risposta al memo #{memo_db['id']} ('{memo_db['titolo']}') già archiviato nel DB!")
                testo_integrato = memo_db["testo_originale"] + f"\n\n[Integrazione del {datetime_now_str()}]: {item['testo_originale']}"
                link_effettivo = memo_db["link_originale"] or item["link_originale"]

                testo_per_ai = testo_integrato
                titolo_suggerito = memo_db["titolo"]
                if link_effettivo:
                    testo_per_ai, titolo_suggerito = web_scraper.prepara_prompt_per_ai(link_effettivo, testo_utente=testo_integrato)

                print(f"Rielaborazione AI per memo integrato #{memo_db['id']}...")
                analisi_ai = ai_processor.analizza_testo(testo_per_ai, titolo_suggerito=titolo_suggerito)

                titolo = analisi_ai.get("titolo", memo_db["titolo"])
                riassunto = analisi_ai.get("riassunto", memo_db["riassunto"])
                categoria = analisi_ai.get("categoria", memo_db.get("categoria", "Altro"))
                priorita = int(analisi_ai.get("priorita", memo_db.get("priorita", 3)))
                data_promemoria = analisi_ai.get("data_promemoria", memo_db.get("data_promemoria"))
                tags_str = ", ".join(analisi_ai.get("tags", []))

                conn = database.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE memo
                    SET titolo = ?, riassunto = ?, testo_originale = ?, link_originale = ?, tags = ?, categoria = ?, priorita = ?, data_promemoria = ?
                    WHERE id = ?
                ''', (titolo, riassunto, testo_integrato, link_effettivo, tags_str, categoria, priorita, data_promemoria, memo_db["id"]))
                conn.commit()
                conn.close()

                print(f"✅ [AGGIORNATO] Memo #{memo_db['id']} ('{titolo}') [Cat: {categoria} | P{priorita}] aggiornato!\n")

                if item["percorso_file"] and os.path.exists(item["percorso_file"]):
                    try:
                        os.remove(item["percorso_file"])
                    except Exception:
                        pass
                continue

        # Caso C: Messaggio radice autonomo
        cluster_batch[item["msg_id"]] = item

    # 3. Elaborazione AI e Salvataggio dei memo radice
    for msg_id, memo in cluster_batch.items():
        tipo_contenuto = memo["tipo_contenuto"]
        testo_originale = memo["testo_originale"]
        link_originale = memo["link_originale"]
        percorso_file = memo["percorso_file"]

        testo_per_ai = testo_originale
        titolo_suggerito = ""

        # Arricchimento web scraping se è presente un link
        if link_originale:
            print(f"[LINK] Rilevato link: {link_originale}. Estrazione contenuto in corso...")
            testo_per_ai, titolo_suggerito = web_scraper.prepara_prompt_per_ai(link_originale, testo_utente=testo_originale)

        print(f"Elaborazione AI per memo tipo '{tipo_contenuto}' (Msg #{msg_id})...")
        analisi_ai = ai_processor.analizza_testo(testo_per_ai, titolo_suggerito=titolo_suggerito)

        titolo = analisi_ai.get("titolo", "Senza Titolo")
        riassunto = analisi_ai.get("riassunto", "")
        categoria = analisi_ai.get("categoria", "Altro")
        priorita = int(analisi_ai.get("priorita", 3))
        data_promemoria = analisi_ai.get("data_promemoria")
        tags_str = ", ".join(analisi_ai.get("tags", []))

        data_creazione = memo.get("data_creazione") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO memo (tipo_contenuto, titolo, riassunto, testo_originale, link_originale, tags, categoria, priorita, telegram_message_id, data_promemoria, data_creazione)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tipo_contenuto, titolo, riassunto, testo_originale, link_originale, tags_str, categoria, priorita, msg_id, data_promemoria, data_creazione))
        conn.commit()
        conn.close()

        nota_promemoria = f" | 📅 {data_promemoria}" if data_promemoria else ""
        print(f"[OK] Salvato memo #{cursor.lastrowid}: '{titolo}' [Cat: {categoria} | P{priorita}{nota_promemoria} | Tags: {tags_str}]\n")

        # Pulizia file temporaneo
        if percorso_file and os.path.exists(percorso_file):
            try:
                os.remove(percorso_file)
            except Exception as e:
                print(f"Avviso: impossibile eliminare {percorso_file}: {e}")

    # Conferma a Telegram che tutti gli update del batch sono stati elaborati
    if max_update_id > 0:
        await bot.get_updates(offset=max_update_id + 1)

    print("[COMPLETATO] Sincronizzazione completata con successo!")

def datetime_now_str():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M")

if __name__ == "__main__":
    asyncio.run(scarica_e_elabora())