import streamlit as st

def render_quick_cheatsheet_sidebar():
    """Mostra un popover compatto nella barra laterale con scorciatoie e comandi rapidi."""
    with st.popover("💡 Scorciatoie & Legenda Rapida", use_container_width=True):
        st.markdown("#### ⚡ Trucchi Rapidi Telegram")
        st.markdown("""
        * **Priorità Alta (P1):** Includi `!p1`, `p1:` o `#urgente` nel messaggio o nota vocale.
        * **Priorità Media (P2):** Includi `!p2` o `p2:`.
        * **Funzione "Rispondi" (Reply-To):** Invia una foto/link e poi *Rispondi* con una nota vocale per aggregare tutto in un unico memo!
        """)
        st.markdown("---")
        st.markdown("#### 🎨 Legenda Priorità")
        st.markdown("""
        * 🔴 **P1 (Urgente):** Scadenze imminenti o note critiche.
        * 🟡 **P2 (Importante):** Da fare o approfondire a breve.
        * ⚪ **P3 (Normale):** Idee, letture, appunti generali.
        """)
        st.markdown("---")
        st.markdown("#### ⌨️ Tasti di Scelta Rapida")
        st.markdown("""
        * **`TAB`**: Salta tra i campi e pulsanti con bordo ad alto contrasto.
        * **`R`**: Ricarica istantaneamente l'interfaccia.
        * **`Barra Spazio`**: Seleziona o attiva il pulsante/checkbox corrente.
        """)

def render_scheda_guida():
    """Rende la guida utente completa e interattiva all'interno della dashboard."""
    st.markdown("""
    <div style="padding: 10px 0 20px 0;">
        <h2 style="margin: 0; font-size: 1.8rem; font-weight: 700; color: inherit;">📖 Guida all'Utilizzo di Astro_KW MemoBot</h2>
        <p style="margin: 5px 0 0 0; opacity: 0.85; font-size: 1.05rem;">
            Il tuo Secondo Cervello personale: cattura note vocali, link, foto e pensieri su Telegram, organizza tutto con AI locale e sincronizza le scadenze con Google Calendar in totale riservatezza.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🚀 1. Flusso Quotidiano: Da Smartphone a PC", expanded=True):
        st.markdown("""
        Il cuore di **Astro_KW MemoBot** è non interrompere le tue attività quotidiane:
        
        1. **Durante il giorno (su smartphone):** Invia qualsiasi appunto alla tua chat privata del bot su Telegram:
           * 🎙️ Un pensiero registrato a voce mentre cammini o guidi.
           * 🔗 Un link da YouTube, Instagram, X o un articolo del web.
           * 📸 Una foto di uno scontrino, un volantino, una fattura o una schermata.
           * ✍️ Un messaggio di testo veloce.
        2. **La sera (o quando accendi il computer):**
           * Apri la schermata web di MemoBot.
           * Premi il pulsante **`🔄 Sincronizza ora con Telegram`** nella barra laterale sinistra.
        3. **Elaborazione Locale Zero-Cloud:**
           * Il tuo modello locale (**Qwen 2.5 14B**) e il motore **Whisper** estraggono automaticamente un titolo sintetico, un riassunto dettagliato, la categoria tematica, le priorità (P1/P2/P3) e le eventuali scadenze orarie o di data.
           * **Nessun dato viene mai inviato a server esterni:** privacy assoluta e funzionamento anche offline (dopo la sincronizzazione).
        """)

    with st.expander("🎙️ 2. Note Vocali, Trascrizione & Calendario Intelligente", expanded=False):
        st.markdown("""
        Il motore di trascrizione **Whisper** integrato con **ffmpeg** ascolta i tuoi file vocali in italiano con la massima fedeltà:
        
        * **Linguaggio Naturale:** Puoi parlare liberamente senza dover usare una sintassi rigida. Ad esempio:
          * *"Ricordami giovedì prossimo alle quindici di richiamare l'assicurazione per la polizza auto"*
          * *"Domani sera cena con Marco alle venti e trenta alla trattoria del centro"*
          * *"Dopodomani fare la spesa"*
        * **Calendario di Riferimento Settimanale:** MemoBot inietta dinamicamente la tabella delle date correnti nel prompt di intelligenza artificiale. Di conseguenza, frasi come *"martedì prossimo"* o *"venerdì"* vengono collegate al giorno corretto del calendario reale, senza mai confondere passati o futuri.
        * **Eventi con orario vs Tutto il giorno:** Se indichi un orario (es. *"alle 15:30"*), MemoBot pianifica l'evento a quell'ora esatta; se indichi solo il giorno (es. *"lunedì"*), l'evento viene salvato come scadenza dell'intera giornata.
        """)

    with st.expander("⚡ 3. Comandi Rapidi & Funzione 'Rispondi' (Reply-To)", expanded=False):
        st.markdown("""
        Puoi pilotare l'intelligenza artificiale del bot con semplici scorciatoie nei tuoi messaggi Telegram:
        
        #### Forzare le Priorità
        * **Priorità 1 (Urgente - Rosso):** Scrivi o detta `!p1`, `p1:` o `#urgente`. MemoBot contrassegnerà il memo con il badge rosso di massima urgenza.
        * **Priorità 2 (Importante - Giallo):** Scrivi `!p2` o `p2:`.
        * **Priorità 3 (Normale - Grigio):** Predefinita se non ci sono scadenze o urgenze esplicite.

        #### La Magia della Funzione "Rispondi" (Reply-To)
        Hai trovato un link interessante o hai scattato una foto e vuoi aggiungere una nota vocale di commento prima che venga elaborata?
        1. Invia il link o l'immagine nella chat Telegram.
        2. Tieni premuto sul messaggio inviato e seleziona **"Rispondi" (Reply)**.
        3. Registra la tua nota vocale di spiegazione e inviala.
        4. Al momento della sincronizzazione, MemoBot riconoscerà che l'audio si riferisce a quel link/foto e **fonderà tutto in un unico memo coerente**, evitando doppioni frammentati!
        """)

    with st.expander("📅 4. Agenda & Sincronizzazione Google Calendar (FabMemoBot)", expanded=False):
        st.markdown("""
        MemoBot dialoga direttamente con le API ufficiali di **Google Calendar** tramite autenticazione sicura OAuth 2.0:
        
        * **Calendario Dedicato:** Tutti gli eventi vengono inseriti nel calendario dedicato **`FabMemoBot`**, mantenendo pulito e separato il tuo calendario personale principale.
        * **Sincronizzazione in 1 Clic:**
          * Nella scheda **`📅 Agenda & Scadenze`**, sotto ciascun memo con data compare il pulsante **`📅 Sincronizza su FabMemoBot`**.
          * Basta un clic: l'evento compare istantaneamente sul tuo smartphone e PC con titolo, riassunto e link alla fonte.
        * **Sincronizzazione di Gruppo (Batch Sync):**
          * Se hai più memo con scadenze non ancora inserite nel calendario, in cima alla scheda compare un avviso con il pulsante:  
            **`🚀 Sincronizza tutte (N) su FabMemoBot`**. Con un solo clic, carica l'intera lista di scadenze in sequenza.
        * **Stato Sincronizzato:** I memo già registrati su Google Calendar mostrano il badge verde **`✅ Sincronizzato su FabMemoBot`**.
        """)

    with st.expander("🔭 5. Astro_KW Radar: Chatta con le tue Note (RAG Locale)", expanded=False):
        st.markdown("""
        * **Cos'è Astro_KW Radar:** È il tuo assistente AI proattivo. Puoi dialogare in linguaggio naturale ponendo qualsiasi domanda sui tuoi appunti personali.
        * **Elaborazione 100% Locale e Privata:** Radar interroga SQLite direttamente sulla tua macchina ed elabora le risposte con **Qwen 2.5 14B** in locale tramite Ollama. Nessun dato lascia il tuo PC.
        * **Morfologia & Stemming Italiano:** Grazie al motore di stemming morfologico integrato, Radar comprende le radici delle parole: domande con plurali come *"quali note parlano di **libri**?"* troveranno con precisione sia note con *"audiolibri"* sia note con *"libro"* al singolare.
        * **Consapevolezza di Stato e Posizione ("Dove si trova?"):** Radar sa sempre in quale scheda si trova ogni appunto (*"Nella scheda 📦 Archivio sotto la categoria Cultura"* o *"Tra i compiti attivi nella scheda Lavoro"*), guidandoti all'istante verso la nota cercata.
        * **Il Cestino come Salvagente Cognitivo:** Le note nel cestino vengono scansionate come rete di sicurezza: se chiedi di un memo scartato per errore, Radar te lo trova e ti avvisa esplicitamente che si trova nel **🗑️ Cestino** pronto per essere ripristinato (mentre non lo includerà mai quando chiedi di compiti o agende attive).
        * **Fonti Consultate Interattive:** Sotto ogni risposta generata, il menu a scomparsa **`📚 Fonti consultate`** ti mostra le schede interattive di ciascun memo esaminato: puoi espanderle con un clic per leggere subito il riassunto, aprire il link web originale o consultare il testo senza uscire dalla chat.
        * **Filtri di Contesto:** Puoi restringere la ricerca a una specifica categoria (es. solo *Lavoro* o solo note *P1 Urgenti*).
        """)

    with st.expander("🗂️ 6. Gestione Archivio, Cestino & Eliminazione Protetta", expanded=False):
        st.markdown("""
        * **Inbox Zero & Archiviazione Note:**
          * I memo nascono come elementi "vivi" da elaborare, leggere o completare.
          * Una volta terminato un compito o approfondito un link/foto, clicca su **`📦 Archivia`** sotto il memo.
          * La nota viene rimossa dalle schede dei compiti attivi (*Tutti, Lavoro, Sport, ecc.*) e spostata nella scheda dedicata **`📦 Archivio`**.
          * Il badge della priorità viene sostituito dal pallino bianco neutro **`⚪ [A]`**, togliendo urgenza visiva ma preservando ogni dettaglio.
        * **Ripristino dall'Archivio con 1 Clic:**
          * Nella scheda **`📦 Archivio`**, sotto ogni memo trovi il tasto **`↩️ Ripristina`** per riportare la nota tra i compiti attivi in qualunque momento.
        * **Cestino & Protezione dalle Cancellazioni Accidentali:**
          * Quando elimini un memo dalle schede attive o dall'archivio, la cancellazione **NON è mai immediata né irreversibile**: il memo viene spostato in sicurezza nel **`🗑️ Cestino`** con contrassegno `🗑️ [CESTINATO]`.
          * Nel **Cestino**, puoi esaminare tutte le note scartate e hai a disposizione:
            * **`↩️ Ripristina Memo`** (sia singolo che massivo per selezioni multiple) per recuperare qualsiasi appunto rimosso per errore.
            * **`🔥 Elimina per Sempre`** (con richiesta esplicita di conferma irreversibile) per i singoli memo.
            * **`🔥 Svuota Cestino`** nella barra degli strumenti per ripulire definitivamente tutto il cestino in un solo colpo.
        * **Azioni di Gruppo (Bulk Actions):**
          * Spunta le caselle di controllo dei memo che vuoi gestire contemporaneamente.
          * Nelle schede attive puoi usare il pulsante **`📦 Archivia ({N})`** o **`🗑️ Cestina ({N})`**.
          * Nella scheda Cestino puoi usare **`↩️ Ripristina ({N})`** o **`🔥 Svuota Cestino`**.
        * **Modifica sul posto:** Cliccando su un memo, puoi espanderlo e modificare titolo, riassunto, categoria o priorità e salvare con il tasto **`💾 Salva Modifiche`**.
        """)

    with st.expander("🎨 7. Accessibilità (WCAG AAA), Ipovisione & Scorciatoie da Tastiera", expanded=False):
        st.markdown("""
        Astro_KW MemoBot è progettato per essere pienamente accessibile secondo le linee guida **WCAG AAA**:
        
        * **Temi ad Alto Contrasto:**
          * **Alto Contrasto (WCAG AAA - Ipovisione):** Sfondo nero puro (`#000000`), testo bianco (`#ffffff`) e accenti giallo sole brillante (`#ffff00`) con un rapporto di contrasto reale superiore a **19:1**.
          * **Carta & Inchiostro (Sepia / Chiaro):** Massimo riposo per gli occhi durante le ore diurne senza abbagliamento da luce blu.
        * **Caratteri Tipografici Inclusivi:**
          * **Atkinson Hyperlegible:** Creato dal *Braille Institute of America*, distingue senza ambiguità caratteri speculari o simili (come `1`, `I`, `l`, `0`, `O`) per facilitare chi ha deficit visivi o dislessia.
          * **Lexend:** Ottimizzato scientificamente per ridurre l'affaticamento visivo.
        * **Navigazione da Tastiera per Ausili Motori:**
          * **`TAB`**: Salta in sequenza tra tutti i campi, pulsanti e schede. Quando la funzione è attiva, l'elemento selezionato viene circondato da un anello di focus spesso e ben visibile.
          * **`Barra Spaziatrice` o `Invio`**: Attiva il pulsante selezionato o spunta la casella.
          * **`R`**: Tasto rapido per ricaricare la pagina senza toccare il mouse.
        * **Scalatura Testo:** Puoi ingrandire l'intero cruscotto fino al **140%** tramite lo slider nella barra laterale sinistra.
        """)

    with st.expander("📲 8. Condivisione Rapida & Esportazione Dati", expanded=False):
        st.markdown("""
        * **Tasto "Condividi / Copia":** Sotto a ogni memo trovi il tasto **`📲 Condividi / Copia`**. Aprendolo, trovi:
          * Una scheda formattata con Titolo, Riassunto e Link pronta per essere copiata con 1 clic negli appunti.
          * Due pulsanti diretti: **`💬 WhatsApp`** e **`✈️ Telegram`** per inoltrare al volo il promemoria a un familiare, collega o collaboratore.
        * **Esportazione Archivio Completo:** Nella barra laterale sinistra (sezione *Esporta Archivio*), puoi scaricare l'intero database in 3 formati:
          * **📄 CSV (Excel):** Per fogli di calcolo e analisi dati.
          * **📦 JSON:** Per backup tecnici o integrazioni con altri applicativi.
          * **📝 Markdown:** Per archivio documentale leggibile o importazione in Obsidian / Notion.
        """)

    with st.expander("🤖 9. Motori AI: Locale (Privacy Assoluta) vs Cloud (Universale per Qualsiasi PC)", expanded=False):
        st.markdown("""
        MemoBot è completamente **agnostico rispetto al motore di intelligenza artificiale**: puoi scegliere la modalità ideale per le tue esigenze e per il tuo computer direttamente dalla barra laterale sinistra (sezione *🤖 Motore AI*):
        
        * **🏠 Modalità Sovrana / Privacy 100% (Ollama Locale):**
          * **Zero Cloud:** Nessun dato, testo, audio o foto esce mai dal tuo PC.
          * **Modello Testo:** `Qwen 2.5 14B` (o `7B` per schede con meno VRAM).
          * **Visione & Audio:** Vision locale (`Qwen 2.5-VL`) e trascrizione con Whisper locale e ffmpeg.
          * **Ideale per:** Chi possiede un PC con GPU dedicata e desidera riservatezza totale e funzionamento offline.
        
        * **☁️ Modalità Universale / Cloud (Nessun Hardware Potente Richiesto):**
          * **Google Gemini (Consigliato Gratuito):** Con una chiave API gratuita da [Google AI Studio](https://aistudio.google.com/), puoi usare `Gemini 1.5/2.0 Flash` a costo zero, con velocità istantanea e precisione impeccabile.
          * **Groq (Ultra-Veloce):** Genera risposte e trascrive audio in meno di 1 secondo con Llama 3.3 e Whisper Cloud ultra-veloce.
          * **OpenAI (ChatGPT):** Per chi ha già un account OpenAI con `gpt-4o-mini`.
          * **OpenRouter:** Unico account per accedere a decine di modelli (Claude 3.5 Sonnet, DeepSeek, Mistral, ecc.).
          * **Ideale per:** Amici, collaboratori o chi usa un portatile leggero senza scheda grafica dedicata, senza bisogno di installare Ollama o pesi giganti.
        
        * **Test Connessione in 1 Clic:** Dalla barra laterale puoi premere **`🧪 Testa Connessione AI`** in qualsiasi momento per verificare lo stato di risposta del tuo motore.
        """)

    st.markdown("---")
    st.caption("Astro_KW MemoBot — Progetto Assistivo Locale & Privacy-First. Licenza aperta Copyleft GNU GPLv3.")
