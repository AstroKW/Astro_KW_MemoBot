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
        
        > ⏰ **Importante: La Finestra di Conservazione di 24 Ore di Telegram**  
        > L'infrastruttura ufficiale dei Bot di Telegram trattiene i messaggi non letti nella propria coda di ricezione per un **massimo di 24 ore**.  
        > * **Consiglio d'uso:** Effettua una sincronizzazione serale o quotidiana ogni volta che accendi il PC.  
        > * **Cosa fare se passano più giorni senza sincronizzare?** Nessun problema: se nella chat di Telegram hai appunti o foto inviati più di 24 ore fa che non sono ancora stati scaricati, basta semplicemente **selezionarli su Telegram, fare "Inoltra" reinviandoli alla stessa chat del bot** e poi premere **`🔄 Sincronizza ora con Telegram`**: verranno elaborati all'istante!
        
        3. **Elaborazione Locale Zero-Cloud:**
           * Il tuo modello locale (**Qwen 2.5 14B**) e il motore **Whisper** estraggono automaticamente un titolo sintetico, un riassunto dettagliato, la categoria tematica, le priorità (P1/P2/P3) e le eventuali scadenze orarie o di data.
           * Le immagini e gli screenshot vengono analizzati dal modello Vision locale (**Qwen 2.5-VL**), compressi e salvati nella cartella `allegati/`.
           * **Visualizzazione Proporzionata & Controllata:** All'interno del memo puoi aprire **`📷 Visualizza Immagine Allegata`** e scegliere la dimensione ideale (*Smartphone 380px*, *Medio 540px* o *100% Intero*), evitando che schermate verticali del telefono esplodano a tutto schermo.
           * **Tasto `🔍 Rianalizza con OCR`:** Se la foto era stata sincronizzata mentre il modello Vision era spento o non ha risposto in tempo, basta premere questo pulsante per rilanciare all'istante l'analisi OCR e rigenerare titolo e riassunto del memo!
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

    with st.expander("🔭 5. Astro_KW Radar: Chatta con le tue Note (RAG Locale & Persistenza)", expanded=False):
        st.markdown("""
        * **Cos'è Astro_KW Radar:** È il tuo assistente AI proattivo. Puoi dialogare in linguaggio naturale ponendo qualsiasi domanda sui tuoi appunti personali.
        * **Elaborazione 100% Locale e Privata:** Radar interroga SQLite direttamente sulla tua macchina ed elabora le risposte con **Qwen 2.5 14B** in locale tramite Ollama (o con il provider cloud che hai scelto). Nessun dato lascia il tuo PC.
        * **Cronologia Persistente & Gestione Sessioni (SQLite):**
          * Le tue conversazioni con Radar **non vanno più perse** quando ricarichi la pagina (`F5`), chiudi il browser o riavvii il computer!
          * Ogni discussione viene salvata in modo sicuro nel database SQLite locale e può essere ripresa in qualunque momento tramite il menu a tendina delle sessioni.
          * Puoi rinominare qualsiasi conversazione con il pulsante **`✏️`** per assegnarle un titolo significativo.
        * **⭐ Preferiti & Protezione delle Ricerche Importanti:**
          * Se un'analisi o una sintesi di Radar è particolarmente utile, premi il pulsante **`⭐ Fissata / ☆ Preferita`** per contrassegnarla con la stella.
          * Le chat preferite vengono collocate automaticamente in cima all'elenco e sono protette da cancellazioni involontarie.
        * **🧹 Pulizia Intelligente in 1 Clic:**
          * Nella barra di gestione trovi il tasto **`🧹 Pulizia`**: ti permette di eliminare in un solo colpo tutte le conversazioni temporanee ("usa e getta"), **preservando intatte solo le sessioni con la stella ⭐**.
        * **💾 Salva Risposta come Nuovo Memo (1-Click):**
          * Quando Radar elabora un riepilogo, un piano d'azione o una lista di compiti, sotto la risposta trovi il pulsante **`💾 Salva come nuovo Memo`**.
          * Aprendolo puoi confermare o personalizzare titolo, categoria tematica, priorità (P1/P2/P3) e tag: la sintesi generata dall'AI verrà memorizzata all'istante tra i tuoi memo ufficiali dell'archivio!
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
            * **`🔥 Elimina per Sempre`** (con richiesta esplicita di conferma irreversibile): elimina definitivamente il record dal database e **cancella fisicamente il file dell'immagine allegata** dalla cartella `allegati/`, lasciando il disco pulito e privo di file orfani.
            * **`🔥 Svuota Cestino`** nella barra degli strumenti per ripulire definitivamente tutto il cestino e tutti i relativi allegati in un solo colpo.
        * **Azioni di Gruppo (Bulk Actions) con Toolbar Intelligente:**
          * Spunta le caselle di controllo dei memo che vuoi gestire contemporaneamente oppure usa i pulsanti **`☑️ Tutti`** e **`⬜ Nessuno`** nella barra degli strumenti.
          * **`🏷️ Categoria ({N})`**: tramite un comodo popover, assegna istantaneamente una nuova categoria tematica (*Lavoro, Tecnologia, Famiglia, Spesa, ecc.*) a tutti i memo selezionati, riorganizzandoli all'istante nelle relative schede.
          * **`🎯 Priorità ({N})`**: modifica in un solo clic l'urgenza di tutti i memo selezionati (*🔴 P1 - Alta/Urgente, 🟡 P2 - Media, 🟢 P3 - Normale*).
          * **`📦 Archivia ({N})`**: archivia in blocco i memo completati togliendoli dalle schede attive.
          * **`🗑️ Cestina ({N})`**: sposta i memo selezionati nel Cestino (con popover di conferma sicuro).
          * Nella scheda Cestino puoi usare **`↩️ Ripristina ({N})`** per ripristinare in massa o **`🔥 Svuota Cestino`** per eliminare tutto definitivamente.
        * **Modalità Alta Velocità, Navigazione Lazy & Finestre Modali:**
          * **Navigazione a Pillole Intelligente (Lazy Tabs):** La barra superiore mostra le sezioni come comode pillole con i relativi contatori aggiornati. L'applicazione esegue e renderizza esclusivamente la sezione attiva, tagliando del 90% il lavoro di calcolo del server e del browser.
          * **Finestra di Modifica Modale (`@st.dialog`):** Cliccando su **`✏️ Modifica`** sotto un memo, si apre una comoda finestra modale centrata e spaziosa. I campi di modifica vengono generati on-demand solo per la nota selezionata, mantenendo l'elenco dei memo ultraleggero e istantaneo al clic.
          * Nella barra laterale (*⚙️ Ordinamento & Vista*) puoi scegliere quanti memo mostrare per pagina (**`25 memo`**, **`50 memo`** o **`Tutti`**).
          * Se una sezione contiene più note rispetto al limite scelto, in fondo alla lista trovi i pulsanti rapidi per visualizzare ulteriori memo o mostrare l'elenco completo in 1 clic.
        * **Modifica sul posto:** Cliccando su **`✏️ Modifica`**, puoi aggiornare titolo, categoria, priorità, data promemoria, allegato fotografico e salvare con il tasto **`💾 Salva Modifiche`**.
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

    with st.expander("🎙️ 10. Podcast Personale, Audiolibri & Ascolto in Auto (AntennaPod & Android Auto)", expanded=True):
        st.markdown(r"""
        Trasforma qualsiasi articolo web trovato mentre scorri il telefono in un **podcast personale ad alta fedeltà**, pronto per essere ascoltato mentre guidi con **Android Auto**:
        
        #### Come Funziona il Flusso Quotidiano
        1. **Condividi l'Articolo da Telegram:**
           * Quando trovi un articolo interessante su internet (es. Dagospia, blog, notizie, approfondimenti), condividi il link nella chat privata con il tuo bot su Telegram.
        2. **Sincronizzazione ed Estrazione Intelligente:**
           * Clicca su **`🔄 Sincronizza ora con Telegram`** (o lascia sincronizzare MemoBot): il sistema visita il link, rimuove banner pubblicitari, pop-up dei cookie e testo irrilevante con *Trafilatura*. Include un motore anti-WAF trasparente con browser Chromium nativo per superare i blocchi 403 (Akamai, Cloudflare) tipici di quotidiani e testate aperte (es. Fanpage, Dagospia, ecc.).
        3. **Introduzione Radiofonica Fluida & Narrazione Naturale (Zero Ripetizioni):**
           * Per garantire un ascolto dinamico e piacevole in auto senza l'effetto 'disco rotto', l'introduzione adotta lo stile rassegna stampa radiofonica diretta: recita la *data odierna in italiano*, la *fonte* e il *titolo dell'articolo*, passando subito all'ascolto del testo integrale.
           * Il sistema applica la **deduplicazione intelligente dell'incipit**: rimuove automaticamente dall'inizio del testo estratto il titolo o sottotitolo ripetuto (frequente sui siti di news come Dagospia o Fanpage), facendo iniziare la narrazione vocale direttamente dalla prima frase della storia.
           * Il motore vocale ultra-realistico (voci clonate GPU Coqui XTTS-v2 o Kokoro-82M ONNX su CPU) legge l'articolo con intonazione naturale e priva di qualunque ridondanza.
        4. **Ascolto su Android Auto con AntennaPod:**
           * Apri la scheda **`🎙️ Podcast & Audio`** su MemoBot sul tuo PC.
           * Inquadra il **Codice QR** con l'app gratuita open-source **AntennaPod** sul tuo smartphone.
           * AntennaPod si abbona al tuo feed locale privato (`feed.xml`) e scarica automaticamente le nuove puntate non appena sei collegato al Wi-Fi di casa.
           * Quando sali in macchina e colleghi il telefono ad **Android Auto**, AntennaPod compare sul cruscotto: puoi ascoltare tutti gli articoli in coda con i comandi al volante, senza distrazioni e a schermo spento!
        
        #### Controlli e Personalizzazione
        * **Attivazione/Disattivazione:** Puoi includere o escludere singole puntate dal feed tramite la casella presente nella scheda di ogni memo o nella vista Podcast.
        * **Generazione Manuale su Richiesta:** Se aggiungi un link o vuoi convertire un memo precedente, premi semplicemente il pulsante **`🎙️ Genera Podcast Audio da Link`** presente nel memo.
        * **Creazione da Testo, Caricamento PDF/Immagini, Incolla da Clipboard (Ctrl+V) & Pulizia Saggi:** Nella scheda Podcast puoi aprire il pannello **`✍️ Crea Podcast Audio da Testo Libero, PDF o Appunti (PC)`**:
          * **📋 Incolla Schermata da Appunti (Win+Shift+S / Ctrl+V):** Se usi lo *Strumento di Cattura* di Windows (`Win + Shift + S`) per ritagliare un articolo, una colonna o una pagina, non serve salvare alcun file sul disco! Premi semplicemente il pulsante **`📋 Incolla Schermata da Appunti`** (oppure premi **`Ctrl+V`** sulla pagina): MemoBot recupera l'immagine istantaneamente dalla memoria RAM di Windows, avvia l'OCR Vision locale ed estrae il testo nel riquadro.
          * **Multi-Pagina & Accodamento Sequenziale:** Puoi incollare o trascinare più pagine in sequenza (es. pagina 1, poi pagina 2, ecc.): grazie all'opzione **`➕ Accoda al testo esistente`** il contenuto viene unito in ordine di lettura naturale.
          * **Caricamento Diretto di File:** Puoi trascinare direttamente un **documento PDF** (estratto all'istante con PyMuPDF da pagina 1 alla fine) o uno o più screenshot salvati sul disco.
          * **Ricostruzione Paragrafi PDF & De-hyphenation:** Il tasto **`🧹 Distendi Paragrafi`** unisce le righe spezzate dal copia-incolla delle colonne e ricompone le parole sillabate con trattino (`imposta- \n zione` -> `impostazione`).
          * **Filtro Citazioni Accademiche:** Il tasto **`🎓 Pulisci Citazioni`** rimuove le note numeriche `[1,2]` e le citazioni `(Autore, Anno)`.
          * **✨ Ottimizza Entrambi:** Esegue con 1 clic sia la distensione dei paragrafi che la rimozione delle citazioni per ottenere un testo fluido da audiolibro.
        * **Voci Standard (CPU), Azure Newsreader e Voci Clonate Ultra-Realistiche (GPU):**
          * Dalla barra laterale sinistra (**🎙️ Impostazioni Podcast**) o dalla scheda Podcast puoi scegliere chi leggerà i tuoi articoli:
            * 👩 **Elsa IT (Edge Cloud)**: Voce broadcast Microsoft Azure, massima naturalezza e prosodia italiana perfetta per rassegna stampa e saggi.
            * 👨 **Diego IT (Edge Cloud)**: Voce maschile fluida e giornalistica.
            * 👨 **Nicola** / 👩 **Sara**: Voci sintetiche neurali veloci su CPU (Kokoro-82M).
            * ✨ **Alberto Angela (Clonata GPU)**: Timbro divulgativo, appassionante e rassicurante.
            * ✨ **Gianni Musy (Clonata GPU)**: Timbro profondo, maestoso e teatrale (storica voce di Gandalf e Silente).
            * ✨ **Giuseppe Battiston (Clonata GPU)**: Timbro caldo, avvolgente e colloquiale.
            * ✨ **Voce Femminile 1 (Clonata GPU)**: Timbro radiofonico limpido ed autorevole da rassegna stampa.

        ---

        #### 📁 Gestione File Audio, Peso su Disco e Azioni Massive
        * **Dove risiedono i file:** Tutti i podcast MP3 generati vengono salvati localmente sul tuo PC nella cartella:  
          `D:\MemoBot\podcasts\` (nessun file audio viene inviato a server esterni o cloud).
        * **Download Diretto del File MP3:** Ciascun episodio podcast (sia all'interno della scheda del memo che nella sezione dedicata ai Podcast) dispone del pulsante **`💾 Scarica MP3`**: con un solo clic puoi salvare il file sul computer già con l'estensione corretta `.mp3` e con il titolo reale del memo/podcast, evitando i menu del browser.
        * **Peso e Spazio:** I file sono codificati a **128 kbps a 44.1 kHz**, con un peso costante e ridotto di circa **0.95 MB per minuto di parlato** (~3–4 MB per articoli standard, ~17 MB per lunghi approfondimenti da 18 minuti). L'intero feed di 30-40 episodi occupa complessivamente poco più di 100 MB.
        * **Cancellazione Audio & Integrità del Memo:** Quando un episodio audio viene eliminato, il file `.mp3` viene rimosso fisicamente dal disco liberando spazio, ma **il memo testuale originale (link, riassunto AI, data e note) rimane intatto nel database**.
        * **Azioni Massive nella Scheda Podcast (1 Clic):**
          * **Selezione:** Usa i pulsanti **`☑️ Tutti`** o **`⬜ Nessuno`**, oppure seleziona manualmente gli episodi desiderati tramite la comoda casella `[x]` a sinistra di ciascuna traccia.
          * **`🗑️ Elimina Audio Selezionati`:** Elimina in blocco i file audio di tutte le puntate spuntate con finestra di conferma.
          * **`➕ Nel Feed` / `⏸️ Escludi`:** Abilita o sospende la trasmissione su AntennaPod per l'intero gruppo di puntate selezionate.

        ---

        #### 🎙️ Guida Operativa: Creare e Aggiungere Nuove Voci Personalizzate (Voice Cloning)
        MemoBot ti permette di clonare **qualsiasi voce reale** (un doppiatore celebre, un narratore di audiolibri, un familiare o la tua stessa voce) grazie al motore neurale **Coqui XTTS-v2** accelerato dalla GPU NVIDIA RTX 5070 Ti, con clonazione immediata *Zero-Shot* (senza attese di addestramento).

        ##### 1. Regole d'Oro per il Campione Audio Perfetto
        * **Durata ideale:** tra **15 e 30 secondi** di parlato continuo. Sotto i 10 secondi il modello fatica a cogliere le inflessioni; oltre i 45 secondi non migliora la qualità e rallenta solo il condizionamento acustico.
        * **Pulizia acustica assoluta:** la voce deve essere **completamente priva di musica di sottofondo**, jingle, risate di sottofondo, rumori di traffico o eco ambientale.
        * **Intonazione naturale:** scegli spezzoni in cui la persona parla con ritmo tranquillo e costante (come in un documentario, un'intervista o un audiolibro), evitando momenti recitati ad alta concitazione o sussurrati.
        * **Formati audio supportati:** `.wav`, `.mp3`, `.ogg`, `.flac`, `.m4a` (mono o stereo, campionamento automatico).

        ##### 2. Come Aggiungere la Nuova Voce a MemoBot (2 metodi)
        * **Metodo A (Dalla Dashboard — 1 Clic):**
          1. Apri la barra laterale sinistra (sezione **🎙️ Podcast & Audio**) oppure la scheda principale **🎙️ Podcast**.
          2. Clicca sul riquadro espandibile **`➕ Carica Nuova Voce Campione`**.
          3. Trascina o seleziona il file audio dal tuo PC tramite il pulsante di caricamento.
          4. Assegna il nome desiderato per il narratore (es. *Roberto Pedicini*, *Luca Ward*, *Mia Voce*).
          5. Premi **Salva Campione Voce**: MemoBot normalizzerà il file e lo salverà nella cartella dedicata. La nuova voce comparirà all'istante nel menu a tendina con il prefisso ✨!
        * **Metodo B (Copia Diretta nella Cartella di Sistema):**
          1. Prendi il file audio pronto e copialo direttamente nella cartella `D:\MemoBot\voci\`.
          2. Rinominalo in modo descrittivo usando lettere minuscole e trattini bassi (es. `roberto_pedicini.wav` oppure `voce_amica_elena.mp3`).
          3. Ricarica la dashboard (tasto **F5**): MemoBot effettuerà la scansione automatica e mostrerà la voce tra i narratori disponibili (es. `✨ Roberto Pedicini (Voce Clonata - XTTS GPU)`).

        ##### 3. Suggerimento per le Voci Femminili & Fallback di Genere
        * Se aggiungi una voce femminile, è consigliabile includere parole come *"femminile"*, *"donna"* o un nome proprio femminile nel nome del file (es. `voce_femminile_2.wav` o `elena.wav`).
        * Se per qualsiasi ragione eccezionale la GPU dovesse trovarsi occupata o indisponibile, MemoBot effettuerà un **fallback intelligente di genere**: utilizzerà automaticamente la voce femminile **Sara (`if_sara`)** anziché quella maschile **Nicola (`im_nicola`)**.
        """)

    st.markdown("---")
    st.caption("Astro_KW MemoBot — Progetto Assistivo Locale & Privacy-First. Licenza aperta Copyleft GNU GPLv3.")
