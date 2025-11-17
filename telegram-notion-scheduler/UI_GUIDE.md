# 📱 Telegram-Notion Scheduler UI - Guida d'Uso

## 🚀 Quick Start

### Avviare l'Interfaccia

```bash
bash ~/telegram-notion-scheduler/launch-ui.sh
```

Questo comando:
1. ✅ Avvia il server Flask in background
2. 🌐 Apre l'interfaccia nel browser
3. 📍 Rende disponibile l'API su `http://localhost:5555`

---

## 🎮 Controllo Scheduler

### ▶️ Avvia Scheduler
Avvia il processo scheduler in background. Lo scheduler inizierà a controllare Notion ogni 15 minuti per post con:
- **Status** = `Programmato`
- **Tipo** = `Telegram_testo` o `Telegram_poll`
- **Uscita** = data/ora passata o presente

### ⏹️ Ferma Scheduler
Arresta il processo scheduler. I post programmati non verranno pubblicati finché non lo riavvii.

---

## 🛠️ Gestione & Diagnostica

### 🔍 Verifica Status
Mostra quante istanze dello scheduler sono in esecuzione.

**Output atteso:**
```
✅ ONE scheduler running (correct!)

francesconguyen  4321  0.5  1.2  392324  32456 ??  Ss   14:22  0:01 python3 scheduler.py
```

**Se vedi errori:**
- ❌ Scheduler NOT running → Nessuna istanza attiva
- ⚠️ DUPLICATES DETECTED → Più di 1 istanza (ferma tutto e riavvia)

### 📋 Vedi Log
Mostra gli ultimi 50 log del scheduler. Qui puoi vedere:
- ✅ Post pubblicati con successo
- ❌ Errori di connessione
- ⏳ Check eseguiti e risultati

**Cosa cercare nei log:**
```
✓ Post published successfully: "TELEGRAM - PREMIER NC4000"
Found 1 post(s) to publish
No scheduled posts to publish
```

### 🧪 Test Connessione
Testa la connessione a Notion e Telegram. Esegue `test_connection.py` che verifica:
- ✅ Token Notion valido
- ✅ Bot Telegram funzionante
- ✅ Canale @probavas accessibile

### ⚙️ Vedi Config
Mostra la configurazione del sistema:
- 🔐 Variables d'ambiente (token nascosti)
- 📁 Percorsi dei file
- ⚙️ Versione Python
- 🔍 Status dello scheduler

---

## 📊 Status Section

Mostra lo stato in tempo reale:

```
🔍 Scheduler Status    ✅ Attivo (verde pulsante)
                       ❌ Arrestato (rosso)
                       🔴 Offline (grigio - server non raggiungibile)

📋 Ultimi Log          Timestamp dell'ultimo check eseguito

⏳ Prossimo Check      "Ogni 15 minuti" (fisso)
```

Lo status si aggiorna automaticamente ogni 10 secondi.

---

## 🔗 Link Rapidi

- **📘 Notion Database** - Apre il tuo database Notion nel browser
- **💬 Telegram Channel** - Apre il canale @probavas nel browser

---

## 🐛 Troubleshooting

### Errore: "Offline - Server not reachable"
Il server Flask non è raggiungibile.

**Soluzione:**
```bash
# Ferma il server precedente
pkill -f "scheduler-server.py"

# Riavvia l'UI
bash ~/telegram-notion-scheduler/launch-ui.sh
```

### Errore: "Scheduler is already running"
Stai cercando di avviare lo scheduler ma è già in esecuzione.

**Soluzione:**
```bash
# Vedi quanti processi ci sono
ps aux | grep scheduler.py | grep -v grep

# Se ce ne sono più di 1, fermali tutti
pkill -9 -f "python3 scheduler.py"

# Riavvia uno soltanto
bash ~/telegram-notion-scheduler/launch-ui.sh
# Poi clicca "Avvia Scheduler"
```

### I post non si pubblicano
Controlla i log per errori. I motivi comuni sono:

1. **Post mancante dal database** - Verifica in Notion che il post sia nella lista
2. **Status non è "Programmato"** - Il post ha Status = "Approvato" o altro?
3. **Tipo errato** - Il Tipo non è "Telegram_testo" o "Telegram_poll"?
4. **Uscita nel futuro** - La data/ora di pubblicazione è nel futuro?
5. **Messaggio vuoto** - Il campo Messaggio ha contenuto?

**Accedi ai log:**
1. Clicca "Vedi Log" nell'interfaccia
2. Cerca il titolo del tuo post
3. Leggi l'errore

Esempio di log di successo:
```
2025-11-17 14:00:32 - scheduler - INFO - Processing post: TELEGRAM - PREMIER NC4000
2025-11-17 14:00:32 - scheduler - INFO - ✓ Post published successfully
```

---

## 📱 Accesso all'Interfaccia

### Localmente (consigliato)
Usando lo script:
```bash
bash ~/telegram-notion-scheduler/launch-ui.sh
```

### Manualmente
Apri il file nel browser:
```
file:///Users/francesconguyen/telegram-notion-scheduler/scheduler-launcher.html
```

E assicurati che il server sia in esecuzione:
```bash
cd ~/telegram-notion-scheduler
source venv/bin/activate
python3 scheduler-server.py
```

---

## 🔌 API Endpoints (per sviluppatori)

Se vuoi integrare con altre applicazioni:

```
GET /api/status
→ Ritorna lo stato dello scheduler

POST /api/execute
{
  "action": "start|stop|status|logs|test|config"
}

GET /health
→ Health check del server
```

---

## ⚙️ Configurazione Avanzata

### Cambiare porta del server
Modifica `scheduler-server.py`:

```python
if __name__ == '__main__':
    app.run(host='localhost', port=5555)  # ← Cambia 5555
```

### Disabilitare CORS
Se vuoi limitare da quali host accedere all'API:

```python
# In scheduler-server.py
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
```

### Eseguire in background permanente
Usa `nohup` per mantenere il server in esecuzione:

```bash
cd ~/telegram-notion-scheduler
source venv/bin/activate
nohup python3 scheduler-server.py > server.log 2>&1 &
```

---

## 📞 Supporto

Se riscontri problemi:

1. **Verifica i log** - Clicca "Vedi Log" nell'interfaccia
2. **Controlla la connessione** - Usa "Test Connessione"
3. **Vedi la config** - Usa "Vedi Config" per diagnosticare
4. **Riavvia tutto** - Ferma e riavvia scheduler + server

---

**💡 Pro Tips:**

- ✅ Tieni l'interfaccia aperta in un tab per monitorare lo scheduler
- ✅ Controlla i log periodicamente per eventuali errori
- ✅ Prima di aggiungere post, verifica con "Test Connessione"
- ✅ Usa "Vedi Config" per verificare che i token siano caricati correttamente

**Buona programmazione! 🚀**
