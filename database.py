import sqlite3
from datetime import datetime

DB_NAME = "memobot.db"

CATEGORIE_STANDARD = [
    "Lavoro",
    "Sport",
    "Tempo Libero",
    "Famiglia/Personale",
    "Tecnologia",
    "Cultura/Notizie",
    "Spesa/Acquisti",
    "Altro"
]

def get_connection():
    """Restituisce una connessione al database con row_factory attivo."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inizializza o aggiorna la struttura del database SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabella principale per salvare tutti i memo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_contenuto TEXT NOT NULL,  -- testo, audio, video, link, immagine
            titolo TEXT,
            riassunto TEXT,
            testo_originale TEXT,
            link_originale TEXT,
            tags TEXT,                     -- separati da virgola
            categoria TEXT DEFAULT 'Altro',-- Lavoro, Sport, Tempo Libero, ecc.
            priorita INTEGER DEFAULT 3,    -- 1: Alta/Urgente, 2: Media, 3: Normale
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_promemoria DATETIME,      -- per le notifiche agenda
            stato_notificato INTEGER DEFAULT 0, -- 0: da notificare, 1: notificato
            telegram_message_id INTEGER    -- ID messaggio Telegram originale
        )
    ''')
    
    # Migrazione sicura delle colonne mancanti
    cursor.execute("PRAGMA table_info(memo)")
    colonne = [col[1] for col in cursor.fetchall()]
    
    if "telegram_message_id" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'telegram_message_id'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN telegram_message_id INTEGER")

    if "priorita" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'priorita'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN priorita INTEGER DEFAULT 3")

    if "categoria" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'categoria'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN categoria TEXT DEFAULT 'Altro'")

    if "google_event_id" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'google_event_id'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN google_event_id TEXT")

    # Indici rapidi per performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_tg_id ON memo(telegram_message_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_priorita ON memo(priorita)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_categoria ON memo(categoria)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_gcal ON memo(google_event_id)')
    
    conn.commit()
    conn.close()
    print("[DATABASE] Database 'memobot.db' aggiornato con successo!")

def segna_sincronizzato_gcal(memo_id: int, google_event_id: str) -> bool:
    """Aggiorna il memo salvando l'ID dell'evento Google Calendar associato."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE memo SET google_event_id = ? WHERE id = ?", (google_event_id, memo_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore salvataggio google_event_id per memo #{memo_id}: {e}")
        return False

def trova_memo_per_telegram_id(tg_message_id: int):
    """Cerca se esiste già un memo salvato con un determinato telegram_message_id."""
    if not tg_message_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memo WHERE telegram_message_id = ?", (tg_message_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def elimina_memo(memo_id: int) -> bool:
    """Elimina un memo dal database per ID."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memo WHERE id = ?", (memo_id,))
        conn.commit()
        eliminato = cursor.rowcount > 0
        conn.close()
        return eliminato
    except Exception as e:
        print(f"[DATABASE] Errore eliminazione memo #{memo_id}: {e}")
        return False

def elimina_memo_multipli(memo_ids: list[int]) -> int:
    """Elimina una lista di memo dal database per ID e restituisce il numero di elementi cancellati."""
    if not memo_ids:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in memo_ids)
        cursor.execute(f"DELETE FROM memo WHERE id IN ({placeholders})", tuple(memo_ids))
        conn.commit()
        cancellati = cursor.rowcount
        conn.close()
        return cancellati
    except Exception as e:
        print(f"[DATABASE] Errore eliminazione multipla memo: {e}")
        return 0

def modifica_memo(memo_id: int, titolo: str, riassunto: str, testo_originale: str, categoria: str, priorita: int, tags: str) -> bool:
    """Aggiorna i campi di un memo esistente."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE memo
            SET titolo = ?, riassunto = ?, testo_originale = ?, categoria = ?, priorita = ?, tags = ?
            WHERE id = ?
        ''', (titolo, riassunto, testo_originale, categoria, priorita, tags, memo_id))
        conn.commit()
        modificato = cursor.rowcount > 0
        conn.close()
        return modificato
    except Exception as e:
        print(f"[DATABASE] Errore modifica memo #{memo_id}: {e}")
        return False

if __name__ == "__main__":
    init_db()