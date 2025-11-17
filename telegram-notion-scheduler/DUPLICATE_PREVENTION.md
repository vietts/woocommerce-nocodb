# 🛡️ Prevenzione Duplicati - Telegram Notion Scheduler

## Problema Riscontrato

Il 17 novembre 2025, il post "TELEGRAM - PREMIER NC4000" è stato pubblicato **due volte** sul canale @probavas.

### Causa

Due istanze dello scheduler erano in esecuzione contemporaneamente:
- PID 9698 - avviato alle 12:47
- PID 10390 - avviato alle 13:05

Entrambe hanno trovato il post con `Status="Programmato"` e `Uscita=14:00` (scaduto), e lo hanno pubblicato quasi contemporaneamente prima che uno aggiornasse lo status a "Pubblicato".

## Soluzione Implementata

### 1. **Safety Check nel Codice** ✅

Aggiunto controllo in `scheduler.py` nel metodo `_process_post()`:

```python
# Safety check: prevent duplicate publishing if post already has Pubblicato status
# (guards against multiple scheduler instances)
if post.get("status") == "Pubblicato":
    logger.debug(f"Post already published, skipping: {title}")
    return False
```

Questo previene che lo stesso post venga pubblicato due volte anche se due istanze di scheduler lo processano.

### 2. **Controllo Prima di Avviare lo Scheduler**

Prima di avviare lo scheduler, verifica che non ce ne sia già uno in esecuzione:

```bash
# Controlla se lo scheduler è già in esecuzione
ps aux | grep "scheduler.py" | grep -v grep

# Se ci sono processi, killali
pkill -9 -f "python3 scheduler.py"

# Poi avvia una sola istanza
cd ~/telegram-notion-scheduler
source venv/bin/activate
python3 scheduler.py
```

### 3. **Accorgimenti Per il Futuro**

#### ⚠️ MAI avviare il scheduler più di una volta

❌ **Sbagliato:**
```bash
python3 scheduler.py &  # Avvia in background
python3 scheduler.py &  # Avvia un'altra istanza - DUPLICATA!
```

✅ **Corretto:**
```bash
# Avvia una sola istanza
python3 scheduler.py

# Oppure in background (ma solo UNA volta):
python3 scheduler.py &
ps aux | grep scheduler.py  # Verifica che ce ne sia solo UNA
```

#### ✅ Best Practices

1. **Verifica prima di avviare**
   ```bash
   ps aux | grep scheduler.py | grep -v grep
   ```

2. **Usa uno script di avvio sicuro** (opzionale)
   ```bash
   #!/bin/bash
   # check_and_start_scheduler.sh

   if pgrep -f "python3 scheduler.py" > /dev/null; then
       echo "Scheduler already running (PID: $(pgrep -f 'python3 scheduler.py'))"
       exit 1
   else
       cd ~/telegram-notion-scheduler
       source venv/bin/activate
       python3 scheduler.py &
   fi
   ```

3. **Monitoring periodico**
   ```bash
   # Aggiungi a crontab per verificare ogni ora
   0 * * * * ps aux | grep "python3 scheduler.py" | grep -v grep || echo "Scheduler not running"
   ```

## Impatto

- ✅ **Codice**: Ora previene duplicati automaticamente
- ✅ **Dati**: Post già pubblicati non verranno ripubblicati
- ⚠️ **Manuale**: L'utente deve assicurarsi di avviare UNA SOLA istanza di scheduler

## Nota Storica

**17 Novembre 2025 - 14:00 CET**
- Post "TELEGRAM - PREMIER NC4000" pubblicato 2 volte
- Causa: Due istanze di scheduler in esecuzione
- Soluzione: Killate entrambe, avviata una sola, aggiunto safety check nel codice

---

**Status**: ✅ Mitigato - Protezione contro duplicati implementata nel codice
