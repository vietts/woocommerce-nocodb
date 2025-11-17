# ✅ Setup Completo - Telegram Notion Scheduler

## 📊 Status

| Componente | Status |
|-----------|--------|
| **Notion Connection** | ✅ Verificata |
| **Telegram Connection** | ✅ Verificata |
| **Message Publishing** | ✅ Testata |
| **Filtering by Type** | ✅ Implementato |
| **Scheduler Logic** | ✅ Completo |

---

## 🚀 Come Usare

### Step 1: Creare i Post su Notion

1. Apri il tuo database Notion
2. Aggiungi un nuovo record con questi campi:

```
Nome:                 "Titolo del Post"
Messaggio:            "Contenuto che verrà pubblicato su Telegram"
Tipo:                 Telegram_testo  (o Telegram_poll)
Uscita:               [Data/ora attuale o passata - timezone Roma]
Status:               Programmato
```

**Leggi la guida completa:** `GUIDA_NOTION.md`

### Step 2: Avviare lo Scheduler

```bash
cd ~/telegram-notion-scheduler
source venv/bin/activate
python3 scheduler.py
```

Il scheduler:
- ✅ Controlla i post ogni 15 minuti
- ✅ Pubblica i post scaduti su Telegram
- ✅ Aggiorna lo stato su Notion da "Programmato" a "Pubblicato"
- ✅ Scrive tutti i log in `scheduler.log`

### Step 3: Verificare su Telegram

Apri il canale `@probavas` e dovresti vedere i tuoi post!

---

## 📁 Struttura Progetto

```
telegram-notion-scheduler/
├── .env                          # Credenziali (PROTETTO)
├── .gitignore                    # Per proteggere .env
├── requirements.txt              # Dipendenze Python
├── scheduler.py                  # Main scheduler (avvia questo!)
├── notion_handler.py             # Client Notion
├── telegram_handler.py           # Client Telegram
├── test_connection.py            # Test veloce connessioni
├── test_telegram_post.py         # Test invio Telegram
├── GUIDA_NOTION.md              # Guida creare post
├── SETUP_COMPLETO.md            # Questo file
└── README.md                     # Docs generali
```

---

## 🔧 Filtri Automatici

Lo scheduler pubblica SOLO i post che hanno:

✅ **Status** = `Programmato`
✅ **Tipo** = `Telegram_testo` OPPURE `Telegram_poll`
✅ **Uscita** = data/ora attuale o nel passato (timezone: Roma)

---

## 📊 Tipi di Post Supportati

### 1️⃣ POST DI TESTO (Telegram_testo)

```
Tipo:      Telegram_testo
Messaggio: "Ciao a tutti!"
Risultato: Solo il testo su Telegram
```

### 2️⃣ POST CON IMMAGINE (Telegram_testo + Immagine URL)

```
Tipo:         Telegram_testo
Messaggio:    "Guarda questa foto!"
Immagine URL: https://example.com/foto.jpg
Risultato:    Immagine + testo su Telegram
```

### 3️⃣ POLL (Telegram_poll)

```
Tipo:           Telegram_poll
Poll Domanda:   "Quale colore preferisci?"
Poll Opzioni:   ["Rosso", "Blu", "Verde"]
Risultato:      Poll su Telegram
```

---

## 🐛 Troubleshooting

### ❌ Il post non viene pubblicato

Verifica checklist:
1. ✅ Campo **Stato** = `Programmato` (case-sensitive)
2. ✅ Campo **Tipo** = `Telegram_testo` o `Telegram_poll` (case-sensitive)
3. ✅ Campo **Data Pubblicazione** è nel passato/presente
4. ✅ Campo **Messaggio** non è vuoto (per testo/immagine)
5. ✅ Campo **Poll Domanda** e **Poll Opzioni** riempiti (per poll)

### ❌ Messaggio vuoto su Telegram

Controlla che il campo **Messaggio** abbia contenuto su Notion.

### ❌ Poll non funziona

- Tipo deve essere esattamente `Telegram_poll`
- Poll Opzioni deve essere JSON: `["Opzione1", "Opzione2", ...]`
- Almeno 2 opzioni, massimo 10

### ❌ Immagine non carica

- URL deve essere accessibile (prova da browser)
- Tipo deve essere `Telegram_testo` (per mostrare immagine)
- Immagine URL deve avere il link completo con `https://`

---

## 📋 Variabili Ambiente (.env)

```env
# Telegram
TELEGRAM_BOT_TOKEN=[REDACTED]
TELEGRAM_CHANNEL=@probavas

# Notion (nuova API 2025-09-03)
NOTION_TOKEN=[REDACTED]
NOTION_DATA_SOURCE_ID=24bb39b7-c6a5-4d71-aef9-fef506466d14

# Configurazione
NOTION_TYPE_FIELD=Tipo
SCHEDULER_INTERVAL_MINUTES=15
LOG_LEVEL=INFO
```

⚠️ **ATTENZIONE:** Non condividere il `.env` con nessuno!

---

## 🌐 Deployment

### Option 1: Railway (consigliato)

```bash
# 1. Push su GitHub
git add .
git commit -m "Telegram-Notion Scheduler"
git push origin main

# 2. Su Railway:
# - Connetti il repo GitHub
# - Comando: python scheduler.py
# - Variabili: aggiungi TELEGRAM_BOT_TOKEN, NOTION_TOKEN, etc.
```

### Option 2: Render

```bash
# Crea novo "Background Worker"
# - Connetti GitHub
# - Comando: python scheduler.py
# - Variabili ambiente
```

### Option 3: GitHub Actions (ogni 15 min)

Crea `.github/workflows/scheduler.yml`:

```yaml
name: Telegram Notion Scheduler
on:
  schedule:
    - cron: '*/15 * * * *'

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python scheduler.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATA_SOURCE_ID: ${{ secrets.NOTION_DATA_SOURCE_ID }}
```

---

## 📝 Log File

I log sono salvati in `scheduler.log`:

```bash
# Visualizza i log in tempo reale
tail -f scheduler.log

# Ultimi 50 log
tail -50 scheduler.log

# Cerca errori
grep ERROR scheduler.log
```

---

## 🎯 Prossimi Step

1. **Crea i post su Notion** seguendo la guida in `GUIDA_NOTION.md`
2. **Avvia lo scheduler:** `python3 scheduler.py`
3. **Verifica su Telegram:** apri `@probavas`
4. **Quando funziona bene:** fai deployment su Railway/Render/GitHub

---

## 📞 Support

- Docs Notion: https://developers.notion.com/
- Docs Telegram: https://python-telegram-bot.readthedocs.io/
- API Notion 2025-09-03: https://developers.notion.com/docs/upgrade-guide-2025-09-03

---

**Sistema Pronto! 🚀**

Inizia a creare post su Notion e guardali pubblicare automaticamente su Telegram!
