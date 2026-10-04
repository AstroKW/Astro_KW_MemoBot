import os
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')
CALENDAR_TARGET_NAME = os.getenv('GOOGLE_CALENDAR_NAME', 'MemoBot')

def is_configured() -> bool:
    """Verifica se il file credentials.json o token.json esiste."""
    return os.path.exists(CREDENTIALS_FILE) or os.path.exists(TOKEN_FILE)

def get_calendar_service():
    """
    Autentica e restituisce il servizio Google Calendar API.
    Gestisce automaticamente il token OAuth 2.0.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"[GCAL] Errore lettura token.json: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[GCAL] Errore refresh token: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"File '{CREDENTIALS_FILE}' non trovato. "
                    "Scarica il file OAuth 2.0 da Google Cloud Console e salvalo come 'credentials.json'."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def trova_o_crea_calendario(service, nome_calendario=CALENDAR_TARGET_NAME) -> str:
    """
    Cerca il calendario dedicato (es. FabMemoBot) tra i calendari dell'utente.
    Se non esiste, lo crea automaticamente. Restituisce il calendarId.
    """
    try:
        calendars_result = service.calendarList().list().execute()
        items = calendars_result.get('items', [])
        
        for cal in items:
            if cal.get('summary', '').strip().lower() == nome_calendario.strip().lower():
                return cal['id']

        # Se non esiste, lo crea
        print(f"[GCAL] Calendario '{nome_calendario}' non trovato. Creazione in corso...")
        nuovo_cal = {
            'summary': nome_calendario,
            'description': 'Calendario dedicato per Astro_KW MemoBot',
            'timeZone': 'Europe/Rome'
        }
        creato = service.calendars().insert(body=nuovo_cal).execute()
        return creato['id']
    except Exception as e:
        print(f"[GCAL] Errore ricerca/creazione calendario '{nome_calendario}': {e}")
        return 'primary'

def inserisci_evento_fabmemobot(titolo: str, data_promemoria_str: str, riassunto: str, link_originale: str = "") -> dict:
    """
    Inserisce un evento direttamente nel calendario 'FabMemoBot'.
    Restituisce un dizionario con l'ID dell'evento e il link htmlLink.
    """
    if not is_configured():
        return {"success": False, "error": "Credenziali Google Calendar non configurate ('credentials.json' mancante)."}

    try:
        service = get_calendar_service()
        calendar_id = trova_o_crea_calendario(service, CALENDAR_TARGET_NAME)

        data_clean = str(data_promemoria_str).strip()
        is_all_day = False

        if len(data_clean) == 10:  # YYYY-MM-DD
            dt_start = datetime.strptime(data_clean, "%Y-%m-%d")
            dt_end = dt_start + timedelta(days=1)
            start_body = {"date": dt_start.strftime("%Y-%m-%d")}
            end_body = {"date": dt_end.strftime("%Y-%m-%d")}
            is_all_day = True
        elif len(data_clean) >= 16:  # YYYY-MM-DD HH:MM
            dt_start = datetime.strptime(data_clean[:16], "%Y-%m-%d %H:%M")
            if dt_start.hour == 0 and dt_start.minute == 0:
                # Se l'orario è 00:00 (non specificato nel memo), imposta come evento 'Tutto il giorno'
                dt_end = dt_start + timedelta(days=1)
                start_body = {"date": dt_start.strftime("%Y-%m-%d")}
                end_body = {"date": dt_end.strftime("%Y-%m-%d")}
                is_all_day = True
            else:
                dt_end = dt_start + timedelta(hours=1)
                start_body = {"dateTime": dt_start.strftime("%Y-%m-%dT%H:%M:00"), "timeZone": "Europe/Rome"}
                end_body = {"dateTime": dt_end.strftime("%Y-%m-%dT%H:%M:00"), "timeZone": "Europe/Rome"}
        else:
            return {"success": False, "error": f"Formato data non valido: '{data_promemoria_str}'"}

        descrizione = f"{riassunto}\n\n[Origine: Astro_KW MemoBot]"
        if link_originale:
            descrizione += f"\nFonte: {link_originale}"

        event_body = {
            'summary': f"📌 {titolo}",
            'description': descrizione,
            'start': start_body,
            'end': end_body,
            'reminders': {
                'useDefault': True
            }
        }

        created_event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        return {
            "success": True,
            "event_id": created_event.get('id'),
            "html_link": created_event.get('htmlLink'),
            "calendar_id": calendar_id
        }
    except Exception as e:
        print(f"[GCAL] Errore inserimento evento: {e}")
        return {"success": False, "error": str(e)}

# Alias per compatibilità
inserisci_evento_calendario = inserisci_evento_fabmemobot
