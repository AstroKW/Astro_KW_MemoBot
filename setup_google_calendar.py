import os
import sys
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')

if not os.path.exists(CREDENTIALS_FILE):
    print(f"ERRORE: '{CREDENTIALS_FILE}' non trovato!")
    sys.exit(1)

print("[1/3] Inizializzazione autorizzazione Google Calendar...")
flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

print("[2/3] Avvio server locale e apertura browser...")
# run_local_server avvia il server locale e tenta di aprire il browser
creds = flow.run_local_server(port=0, prompt='consent')

with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
    token.write(creds.to_json())

print("\n" + "="*50)
print("SUCCESS: Autorizzazione completata con successo!")
print(f"Token salvato in: {TOKEN_FILE}")
print("="*50)
