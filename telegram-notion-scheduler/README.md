# Telegram-Notion Post Scheduler

Automatizza la pubblicazione di post da un database Notion a un canale Telegram.

## 🎯 Caratteristiche

- ✅ Legge post programmati da Notion
- ✅ Pubblica automaticamente su Telegram (Testo, Immagini, Poll)
- ✅ Aggiorna lo stato dei post su Notion
- ✅ Pianificazione ricorrente ogni 15-30 minuti
- ✅ Gestione errori e logging completo
- ✅ Facile deployment su Railway/Render

## 📋 Prerequisiti

- Python 3.8+
- Token Telegram Bot
- Notion Integration Token
- Database Notion configurato

## 🚀 Setup Locale

### 1. Installare dipendenze

```bash
cd telegram-notion-scheduler
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurare credenziali

Il file `.env` è già configurato con le tue credenziali:

```env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHANNEL=@your_channel
NOTION_TOKEN=your_token
NOTION_DATABASE_ID=your_database_id
NOTION_TYPE_FIELD=Tipo
SCHEDULER_INTERVAL_MINUTES=15
LOG_LEVEL=INFO
```

### 3. Verificare setup

```bash
python -c "from notion_client import NotionClient; from telegram_client import TelegramClient; print('✓ Dependencies OK')"
```

## 🧪 Testing

### Test manuale dello scheduler

```bash
python scheduler.py
```

Il programma:
1. ✓ Testerà la connessione a Notion
2. ✓ Testerà la connessione a Telegram
3. ✓ Inizierà a controllare i post ogni 15 minuti
4. ✓ Registrerà tutto in `scheduler.log`

### Creare post di test su Notion

1. Apri il tuo database Notion
2. Crea nuovi record con:
   - **Nome**: Titolo del post
   - **Messaggio**: Contenuto del post
   - **Tipo**: "Testo" / "Immagine+Testo" / "Poll"
   - **Data Pubblicazione**: Ora attuale o passata
   - **Stato**: "Programmato"
   - **Image URL** (se Immagine+Testo): URL dell'immagine
   - **Poll Domanda** (se Poll): La domanda
   - **Poll Opzioni** (se Poll): `["Opzione 1", "Opzione 2", "Opzione 3"]`

### Verificare su Telegram

- Apri il canale `@probavas`
- Verifica che i post siano stati pubblicati
- Controlla i log in `scheduler.log`

## 📚 Database Schema Notion

Il database deve avere questi campi:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| Nome | Title | Titolo del post |
| Messaggio | Rich Text | Contenuto del post |
| Tipo | Select | "Testo" / "Immagine+Testo" / "Poll" |
| Data Pubblicazione | Date | Quando pubblicare |
| Immagine URL | URL | Link immagine (opzionale) |
| Poll Domanda | Text | Domanda del poll (opzionale) |
| Poll Opzioni | Text | JSON array opzioni (opzionale) |
| Stato | Select | "Programmato" / "Pubblicato" / "Errore" |
| Channel ID | Text | @channel (opzionale, di default @probavas) |
| Message ID | Text | ID del messaggio Telegram (auto) |

## 🔧 Gestione degli Errori

- Se un post ha lo stato "Errore", controlla `scheduler.log`
- Errori comuni:
  - **Image URL non valido**: Verifica il link
  - **Poll con meno di 2 opzioni**: Aggiungi almeno 2 opzioni
  - **Canale non raggiungibile**: Verifica che il bot sia admin del canale

## 📋 Log

I log sono salvati in `scheduler.log` con:
- Timestamp
- Livello (INFO, WARNING, ERROR)
- Messaggio dettagliato

Visualizza in tempo reale:
```bash
tail -f scheduler.log
```

## 🌐 Deployment

### Option 1: Railway

1. Push il repository su GitHub
2. Connetti Railway al repository
3. Imposta variabili ambiente in Railway:
   - `TELEGRAM_BOT_TOKEN`
   - `NOTION_TOKEN`
   - Etc.
4. Deploy

### Option 2: Render

1. Crea nuovo "Background Worker"
2. Connetti GitHub
3. Comando: `python scheduler.py`
4. Imposta variabili ambiente

### Option 3: GitHub Actions

Crea `.github/workflows/scheduler.yml`:

```yaml
name: Run Scheduler Every 15 Min
on:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python scheduler.py --run-once
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
```

## 🐛 Troubleshooting

### Errore di connessione a Notion
```
Errore: "Invalid Notion token"
```
→ Verifica il token in `.env`

### Errore di connessione a Telegram
```
Errore: "Unauthorized"
```
→ Verifica il bot token e che il bot sia admin del canale

### No posts trovati
→ Verifica che:
1. Lo Stato sia "Programmato"
2. La Data Pubblicazione sia <= ora attuale
3. Il database ID sia corretto

## 📞 Support

- Docs Telegram: https://python-telegram-bot.readthedocs.io/
- Docs Notion: https://developers.notion.com/

## 📄 License

MIT
