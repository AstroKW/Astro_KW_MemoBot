import os
import sqlite3
from datetime import datetime

DB_NAME = "memobot.db"
ALLEGATI_DIR = "allegati"

def _rimuovi_file_allegato(percorso: str | None):
    """Rimuove fisicamente dal disco il file allegato se esiste."""
    if percorso and os.path.exists(percorso):
        try:
            os.remove(percorso)
            print(f"[ALLEGATI] Rimosso file allegato dal disco: {percorso}")
        except Exception as e:
            print(f"[ALLEGATI] Impossibile eliminare il file {percorso}: {e}")

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
            telegram_message_id INTEGER,   -- ID messaggio Telegram originale
            allegato_path TEXT             -- Percorso locale relativo del file immagine allegato
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

    if "archiviato" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'archiviato'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN archiviato INTEGER DEFAULT 0")

    if "cestinato" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'cestinato'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN cestinato INTEGER DEFAULT 0")

    if "allegato_path" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'allegato_path'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN allegato_path TEXT")

    if "audio_podcast_path" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'audio_podcast_path'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN audio_podcast_path TEXT")

    if "podcast_incluso" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'podcast_incluso'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN podcast_incluso INTEGER DEFAULT 0")

    if "podcast_durata" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'podcast_durata'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN podcast_durata INTEGER DEFAULT 0")

    if "podcast_intro" not in colonne:
        print("[DATABASE] Migrazione: aggiunta colonna 'podcast_intro'...")
        cursor.execute("ALTER TABLE memo ADD COLUMN podcast_intro TEXT")

    # Indici rapidi per performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_tg_id ON memo(telegram_message_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_priorita ON memo(priorita)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_categoria ON memo(categoria)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_gcal ON memo(google_event_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_archiviato ON memo(archiviato)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_cestinato ON memo(cestinato)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memo_podcast ON memo(podcast_incluso)')

    # Tabella sessioni Astro_KW Radar (Chat RAG persistente)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS radar_sessioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titolo TEXT NOT NULL,
            preferito INTEGER DEFAULT 0,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_aggiornamento DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabella messaggi per sessione Radar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS radar_messaggi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sessione_id INTEGER NOT NULL,
            ruolo TEXT NOT NULL,
            contenuto TEXT NOT NULL,
            fonti_json TEXT,
            data_invio DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sessione_id) REFERENCES radar_sessioni(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_radar_msg_sess ON radar_messaggi(sessione_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_radar_sess_pref ON radar_sessioni(preferito)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_radar_sess_data ON radar_sessioni(data_aggiornamento)')
    
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
    """Elimina definitivamente un memo dal database e rimuove eventuali allegati e podcast dal disco."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Recupera percorso dell'allegato e del podcast se presenti
        cursor.execute("SELECT allegato_path, audio_podcast_path FROM memo WHERE id = ?", (memo_id,))
        row = cursor.fetchone()
        allegato_path = row[0] if (row and row[0]) else None
        podcast_path = row[1] if (row and row[1]) else None

        cursor.execute("DELETE FROM memo WHERE id = ?", (memo_id,))
        conn.commit()
        eliminato = cursor.rowcount > 0
        conn.close()

        if eliminato:
            if allegato_path:
                _rimuovi_file_allegato(allegato_path)
            if podcast_path:
                _rimuovi_file_allegato(podcast_path)

        return eliminato
    except Exception as e:
        print(f"[DATABASE] Errore eliminazione memo #{memo_id}: {e}")
        return False

def elimina_memo_multipli(memo_ids: list[int]) -> int:
    """Elimina definitivamente una lista di memo dal database e rimuove i relativi file allegati e podcast dal disco."""
    if not memo_ids:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in memo_ids)

        # Recupera percorsi degli allegati e podcast
        cursor.execute(f"SELECT allegato_path, audio_podcast_path FROM memo WHERE id IN ({placeholders})", tuple(memo_ids))
        file_da_rimuovere = []
        for r in cursor.fetchall():
            if r[0]: file_da_rimuovere.append(r[0])
            if r[1]: file_da_rimuovere.append(r[1])

        cursor.execute(f"DELETE FROM memo WHERE id IN ({placeholders})", tuple(memo_ids))
        conn.commit()
        cancellati = cursor.rowcount
        conn.close()

        for a_path in file_da_rimuovere:
            _rimuovi_file_allegato(a_path)

        return cancellati
    except Exception as e:
        print(f"[DATABASE] Errore eliminazione multipla memo: {e}")
        return 0

def imposta_allegato(memo_id: int, allegato_path: str) -> bool:
    """Associa un file allegato a un memo."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE memo SET allegato_path = ? WHERE id = ?", (allegato_path, memo_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore associazione allegato a memo #{memo_id}: {e}")
        return False

def rimuovi_allegato(memo_id: int) -> bool:
    """Rimuove l'allegato associato a un memo sia dal database che dal disco."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT allegato_path FROM memo WHERE id = ?", (memo_id,))
        row = cursor.fetchone()
        allegato_path = row[0] if (row and row[0]) else None

        cursor.execute("UPDATE memo SET allegato_path = NULL WHERE id = ?", (memo_id,))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()

        if ok and allegato_path:
            _rimuovi_file_allegato(allegato_path)
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore rimozione allegato da memo #{memo_id}: {e}")
        return False

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

def cambia_categoria_multipli(memo_ids: list[int], nuova_categoria: str) -> int:
    """Modifica la categoria di più memo contemporaneamente."""
    if not memo_ids or not nuova_categoria:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in memo_ids)
        cursor.execute(f'''
            UPDATE memo
            SET categoria = ?
            WHERE id IN ({placeholders})
        ''', [nuova_categoria] + memo_ids)
        conn.commit()
        modificati = cursor.rowcount
        conn.close()
        return modificati
    except Exception as e:
        print(f"[DATABASE] Errore cambio categoria multipli: {e}")
        return 0

def cambia_priorita_multipli(memo_ids: list[int], nuova_priorita: int) -> int:
    """Modifica la priorità (1: Alta, 2: Media, 3: Normale) di più memo contemporaneamente."""
    if not memo_ids or nuova_priorita not in [1, 2, 3]:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in memo_ids)
        cursor.execute(f'''
            UPDATE memo
            SET priorita = ?
            WHERE id IN ({placeholders})
        ''', [nuova_priorita] + memo_ids)
        conn.commit()
        modificati = cursor.rowcount
        conn.close()
        return modificati
    except Exception as e:
        print(f"[DATABASE] Errore cambio priorità multipli: {e}")
        return 0

def aggiorna_dettagli_articolo_memo(memo_id: int, titolo: str, riassunto: str = None) -> bool:
    """Aggiorna titolo ed eventuale riassunto del memo se prima non erano disponibili (es. dopo estrazione da link protetto)."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if riassunto:
            cursor.execute('''
                UPDATE memo
                SET titolo = ?, riassunto = ?
                WHERE id = ?
            ''', (titolo, riassunto, memo_id))
        else:
            cursor.execute('''
                UPDATE memo
                SET titolo = ?
                WHERE id = ?
            ''', (titolo, memo_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore aggiornamento dettagli memo #{memo_id}: {e}")
        return False

def imposta_stato_archiviato(memo_id: int, archiviato: bool = True) -> bool:
    """Imposta lo stato di archiviazione (True = archiviato, False = attivo/ripristinato)."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        val = 1 if archiviato else 0
        cursor.execute("UPDATE memo SET archiviato = ? WHERE id = ?", (val, memo_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore cambio stato archiviazione memo #{memo_id}: {e}")
        return False

def imposta_stato_archiviato_multipli(memo_ids: list[int], archiviato: bool = True) -> int:
    """Imposta lo stato di archiviazione per una lista di ID (True = archivia, False = ripristina)."""
    if not memo_ids:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        val = 1 if archiviato else 0
        placeholders = ",".join("?" for _ in memo_ids)
        cursor.execute(f"UPDATE memo SET archiviato = ? WHERE id IN ({placeholders})", (val, *memo_ids))
        conn.commit()
        aggiornati = cursor.rowcount
        conn.close()
        return aggiornati
    except Exception as e:
        print(f"[DATABASE] Errore archiviazione multipla memo: {e}")
        return 0

def sposta_nel_cestino(memo_id: int) -> bool:
    """Sposta un memo nel cestino (soft delete)."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE memo SET cestinato = 1 WHERE id = ?", (memo_id,))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore spostamento nel cestino memo #{memo_id}: {e}")
        return False

def sposta_nel_cestino_multipli(memo_ids: list[int]) -> int:
    """Sposta una lista di memo nel cestino (soft delete)."""
    if not memo_ids:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in memo_ids)
        cursor.execute(f"UPDATE memo SET cestinato = 1 WHERE id IN ({placeholders})", tuple(memo_ids))
        conn.commit()
        spostati = cursor.rowcount
        conn.close()
        return spostati
    except Exception as e:
        print(f"[DATABASE] Errore spostamento multiplo nel cestino: {e}")
        return 0

def ripristina_dal_cestino(memo_id: int) -> bool:
    """Ripristina un memo dal cestino."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE memo SET cestinato = 0 WHERE id = ?", (memo_id,))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore ripristino dal cestino memo #{memo_id}: {e}")
        return False

def ripristina_dal_cestino_multipli(memo_ids: list[int]) -> int:
    """Ripristina una lista di memo dal cestino."""
    if not memo_ids:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in memo_ids)
        cursor.execute(f"UPDATE memo SET cestinato = 0 WHERE id IN ({placeholders})", tuple(memo_ids))
        conn.commit()
        ripristinati = cursor.rowcount
        conn.close()
        return ripristinati
    except Exception as e:
        print(f"[DATABASE] Errore ripristino multiplo dal cestino: {e}")
        return 0

def svuota_cestino() -> int:
    """Elimina definitivamente tutti i memo attualmente nel cestino e rimuove i relativi file allegati dal disco."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Recupera tutti i file allegati e podcast dei memo cestinati
        cursor.execute("SELECT allegato_path, audio_podcast_path FROM memo WHERE cestinato = 1")
        file_da_rimuovere = []
        for r in cursor.fetchall():
            if r[0]: file_da_rimuovere.append(r[0])
            if r[1]: file_da_rimuovere.append(r[1])

        cursor.execute("DELETE FROM memo WHERE cestinato = 1")
        conn.commit()
        eliminati = cursor.rowcount
        conn.close()

        for a_path in file_da_rimuovere:
            _rimuovi_file_allegato(a_path)

        return eliminati
    except Exception as e:
        print(f"[DATABASE] Errore svuotamento cestino: {e}")
        return 0

# ==============================================================================
# GESTIONE PODCAST & AUDIOBOOK (MEMOBOT PODCAST)
# ==============================================================================

def imposta_podcast_memo(memo_id: int, audio_path: str, durata: int, intro: str = "", incluso: int = 1) -> bool:
    """Associa un file podcast audio MP3 a un memo."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE memo
            SET audio_podcast_path = ?, podcast_durata = ?, podcast_intro = ?, podcast_incluso = ?
            WHERE id = ?
        ''', (audio_path, durata, intro, incluso, memo_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore salvataggio podcast per memo #{memo_id}: {e}")
        return False

def rimuovi_podcast_memo(memo_id: int) -> bool:
    """Rimuove l'audio podcast dal memo e cancella il file MP3 da disco."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT audio_podcast_path FROM memo WHERE id = ?", (memo_id,))
        row = cursor.fetchone()
        podcast_path = row[0] if (row and row[0]) else None

        cursor.execute('''
            UPDATE memo
            SET audio_podcast_path = NULL, podcast_durata = 0, podcast_intro = NULL, podcast_incluso = 0
            WHERE id = ?
        ''', (memo_id,))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()

        if ok and podcast_path:
            _rimuovi_file_allegato(podcast_path)
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore rimozione podcast memo #{memo_id}: {e}")
        return False

def rimuovi_podcast_multipli(memo_ids: list[int]) -> int:
    """Rimuove l'audio podcast da più memo contemporaneamente e cancella i file MP3 dal disco."""
    if not memo_ids:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in memo_ids)
        
        # 1. Recupera i file audio da cancellare dal disco
        cursor.execute(f"SELECT audio_podcast_path FROM memo WHERE id IN ({placeholders}) AND audio_podcast_path IS NOT NULL", memo_ids)
        file_audio = [r[0] for r in cursor.fetchall() if r[0]]
        
        # 2. Azzera le colonne podcast nel DB
        cursor.execute(f'''
            UPDATE memo
            SET audio_podcast_path = NULL, podcast_durata = 0, podcast_intro = NULL, podcast_incluso = 0
            WHERE id IN ({placeholders})
        ''', memo_ids)
        conn.commit()
        modificati = cursor.rowcount
        conn.close()
        
        # 3. Elimina fisicamente i file audio MP3 dal disco
        for a_path in file_audio:
            _rimuovi_file_allegato(a_path)
            
        return modificati
    except Exception as e:
        print(f"[DATABASE] Errore rimozione podcast multipli: {e}")
        return 0

def cambia_inclusione_podcast(memo_id: int, incluso: bool) -> bool:
    """Abilita o disabilita l'inclusione di un episodio nel feed RSS del podcast."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        val = 1 if incluso else 0
        cursor.execute("UPDATE memo SET podcast_incluso = ? WHERE id = ?", (val, memo_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[DATABASE] Errore toggle inclusione feed memo #{memo_id}: {e}")
        return False

def cambia_inclusione_podcast_multipli(memo_ids: list[int], incluso: bool) -> int:
    """Modifica lo stato di inclusione nel feed RSS per più episodi contemporaneamente."""
    if not memo_ids:
        return 0
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in memo_ids)
        val = 1 if incluso else 0
        cursor.execute(f'''
            UPDATE memo
            SET podcast_incluso = ?
            WHERE id IN ({placeholders})
        ''', [val] + memo_ids)
        conn.commit()
        modificati = cursor.rowcount
        conn.close()
        return modificati
    except Exception as e:
        print(f"[DATABASE] Errore toggle inclusione podcast multipli: {e}")
        return 0

def ottieni_memo_podcast(solo_inclusi: bool = True) -> list[dict]:
    """Recupera tutti i memo che hanno una traccia audio podcast generata."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if solo_inclusi:
            cursor.execute('''
                SELECT * FROM memo 
                WHERE audio_podcast_path IS NOT NULL AND audio_podcast_path != '' 
                  AND podcast_incluso = 1 AND cestinato = 0
                ORDER BY data_creazione DESC
            ''')
        else:
            cursor.execute('''
                SELECT * FROM memo 
                WHERE audio_podcast_path IS NOT NULL AND audio_podcast_path != '' 
                  AND cestinato = 0
                ORDER BY data_creazione DESC
            ''')
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[DATABASE] Errore recupero memo podcast: {e}")
        return []

def inserisci_memo(tipo_contenuto: str, titolo: str, riassunto: str, testo_originale: str, categoria: str = "Altro", priorita: int = 3, tags: str = "", link_originale: str = "", data_promemoria: str = None, allegato_path: str = None) -> int:
    """Inserisce un nuovo memo nel database SQLite e restituisce il suo ID."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO memo (tipo_contenuto, titolo, riassunto, testo_originale, link_originale, tags, categoria, priorita, data_promemoria, allegato_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tipo_contenuto, titolo, riassunto, testo_originale, link_originale, tags, categoria, priorita, data_promemoria, allegato_path))
        conn.commit()
        memo_id = cursor.lastrowid
        conn.close()
        print(f"[DATABASE] Nuovo memo creato con successo: #{memo_id} - '{titolo}'")
        return memo_id
    except Exception as e:
        print(f"[DATABASE] Errore inserimento nuovo memo: {e}")
        return 0

# ==============================================================================
# GESTIONE SESSIONI & CRONOLOGIA ASTRO_KW RADAR (CHAT RAG)
# ==============================================================================

def crea_sessione_radar(titolo: str = "Nuova Ricerca") -> int:
    """Crea una nuova sessione di chat Radar e restituisce il suo ID."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO radar_sessioni (titolo) VALUES (?)", (titolo,))
        conn.commit()
        sess_id = cursor.lastrowid
        conn.close()
        return sess_id
    except Exception as e:
        print(f"[RADAR] Errore creazione sessione: {e}")
        return 0

def ottieni_sessioni_radar() -> list[dict]:
    """Recupera tutte le sessioni Radar ordinate per preferiti (in cima) e recency."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM radar_sessioni ORDER BY preferito DESC, data_aggiornamento DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[RADAR] Errore recupero sessioni: {e}")
        return []

def ottieni_sessione_radar(sessione_id: int) -> dict | None:
    """Recupera i dettagli di una singola sessione Radar."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM radar_sessioni WHERE id = ?", (sessione_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[RADAR] Errore recupero sessione #{sessione_id}: {e}")
        return None

def rinomina_sessione_radar(sessione_id: int, nuovo_titolo: str) -> bool:
    """Rinomina una sessione Radar."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE radar_sessioni SET titolo = ?, data_aggiornamento = CURRENT_TIMESTAMP WHERE id = ?", (nuovo_titolo, sessione_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[RADAR] Errore rinomina sessione #{sessione_id}: {e}")
        return False

def imposta_preferito_sessione_radar(sessione_id: int, preferito: bool) -> bool:
    """Imposta o rimuove lo stato preferito (stella ⭐) di una sessione."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        val = 1 if preferito else 0
        cursor.execute("UPDATE radar_sessioni SET preferito = ?, data_aggiornamento = CURRENT_TIMESTAMP WHERE id = ?", (val, sessione_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[RADAR] Errore cambio stato preferito sessione #{sessione_id}: {e}")
        return False

def elimina_sessione_radar(sessione_id: int) -> bool:
    """Elimina definitivamente una sessione Radar e tutti i suoi messaggi."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM radar_messaggi WHERE sessione_id = ?", (sessione_id,))
        cursor.execute("DELETE FROM radar_sessioni WHERE id = ?", (sessione_id,))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok
    except Exception as e:
        print(f"[RADAR] Errore eliminazione sessione #{sessione_id}: {e}")
        return False

def svuota_sessioni_non_preferite() -> int:
    """Elimina in blocco tutte le sessioni NON contrassegnate come preferite (⭐)."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM radar_sessioni WHERE preferito = 0")
        ids = [r[0] for r in cursor.fetchall()]
        if not ids:
            conn.close()
            return 0
        
        placeholders = ",".join("?" for _ in ids)
        cursor.execute(f"DELETE FROM radar_messaggi WHERE sessione_id IN ({placeholders})", tuple(ids))
        cursor.execute(f"DELETE FROM radar_sessioni WHERE id IN ({placeholders})", tuple(ids))
        conn.commit()
        cancellate = cursor.rowcount
        conn.close()
        return cancellate
    except Exception as e:
        print(f"[RADAR] Errore pulizia sessioni non preferite: {e}")
        return 0

def salva_messaggio_radar(sessione_id: int, ruolo: str, contenuto: str, fonti: list | None = None) -> int:
    """Salva un messaggio nella sessione Radar e aggiorna il timestamp della sessione."""
    import json
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        fonti_json = json.dumps(fonti, ensure_ascii=False) if fonti else None
        cursor.execute('''
            INSERT INTO radar_messaggi (sessione_id, ruolo, contenuto, fonti_json)
            VALUES (?, ?, ?, ?)
        ''', (sessione_id, ruolo, contenuto, fonti_json))
        msg_id = cursor.lastrowid
        cursor.execute("UPDATE radar_sessioni SET data_aggiornamento = CURRENT_TIMESTAMP WHERE id = ?", (sessione_id,))
        conn.commit()
        conn.close()
        return msg_id
    except Exception as e:
        print(f"[RADAR] Errore salvataggio messaggio sessione #{sessione_id}: {e}")
        return 0

def ottieni_messaggi_sessione_radar(sessione_id: int) -> list[dict]:
    """Recupera la cronologia dei messaggi di una sessione Radar con fonti deserializzate."""
    import json
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM radar_messaggi WHERE sessione_id = ? ORDER BY id ASC", (sessione_id,))
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            f_json = d.get("fonti_json")
            if f_json:
                try:
                    d["fonti"] = json.loads(f_json)
                except Exception:
                    d["fonti"] = []
            else:
                d["fonti"] = []
            rows.append(d)
        conn.close()
        return rows
    except Exception as e:
        print(f"[RADAR] Errore recupero messaggi sessione #{sessione_id}: {e}")
        return []

if __name__ == "__main__":
    init_db()