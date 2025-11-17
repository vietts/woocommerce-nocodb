# 🔐 Lockfile Failsafe System - Documentazione Completa

## 📋 Sommario Esecutivo

Il sistema scheduler ha una **protezione failsafe integrata** che garantisce che **solo una istanza può essere in esecuzione contemporaneamente**.

**Problema Risolto:** "ok però non si capisce mai quante istanze ci sono e se stanno andando"

**Soluzione:** Lockfile-based process locking con verifica PID

---

## ✨ Cosa Fa Il Sistema

### 1. **Garantisce Una Sola Istanza**
```
Tentativo 1: ✅ SUCCESSO - Crea lockfile con PID
Tentativo 2: ❌ RIFIUTATO - Lockfile esiste con PID valido
Tentativo 3: ❌ RIFIUTATO - Stessa ragione
```

### 2. **Rileva Lockfile Stantii Automaticamente**
```
Se il processo con PID nel lockfile è morto:
✅ Rimuove il lockfile stantio
✅ Permette al nuovo processo di acquisire il lock
```

### 3. **Interfaccia Web Accurata**
```
Scheduler Running    → UI mostra "✅ Attivo" (green dot, pulsing)
Scheduler Stopped    → UI mostra "Arrestato" (red dot, static)
```

---

## 🔧 Come Funziona Internamente

### Lockfile Location
```
~/.scheduler.lock  →  /Users/francesconguyen/telegram-notion-scheduler/.scheduler.lock
```

### Contenuto del Lockfile
```
14521
```
(Contiene solo il PID del processo)

### Flow di Avvio dello Scheduler

```
1. scheduler.py avvia
2. Controlla LOCKFILE
   ├─ Se non esiste        → Crea con PID attuale
   ├─ Se esiste
   │  ├─ PID è vivo?       → Rifiuta (esco)
   │  └─ PID è morto?      → Rimuovi, crea nuovo
3. Registra cleanup handlers
4. Inizializza sistema
5. Avvia scheduler job
6. Loop infinito
```

### Cleanup (Quando si ferma)
```
1. Signal handler cattura SIGTERM/SIGINT
2. _release_lock() chiamato
3. Rimuove LOCKFILE
4. Termina processo
```

---

## 📱 Interfaccia Utente

### Stato Scheduler

**Quando è ATTIVO:**
```
🔍 Scheduler Status:   ✅ Attivo  🟢(pulsing)
📋 Ultimi Log:        14:36:12
⏳ Prossimo Check:    Ogni 15 minuti
```

**Quando è ARRESTATO:**
```
🔍 Scheduler Status:   Arrestato  🔴(static)
📋 Ultimi Log:        Nessun log
⏳ Prossimo Check:    Ogni 15 minuti
```

### Comportamento Pulsante 🟢
La palla verde **pulsa** quando lo scheduler è attivo:
```css
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

Questo rende **chiarissimo** che il sistema sta elaborando.

---

## 🚀 Come Usarlo

### Avvia lo Scheduler

**Metodo 1: Da terminale**
```bash
cd ~/telegram-notion-scheduler
source venv/bin/activate
python3 scheduler.py
```

**Metodo 2: Da interfaccia web**
```
1. Apri http://localhost:5555
2. Clicca "▶️ Avvia Scheduler"
3. Guarda il punto verde pulsar e Status cambiar in "✅ Attivo"
```

### Verifica Stato

**Da Web UI:**
```
Lo stato si aggiorna OGNI 10 SECONDI automaticamente
```

**Da Terminale:**
```bash
# Controlla il lockfile
cat .scheduler.lock

# Verifica processo
ps aux | grep "python3 scheduler.py" | grep -v grep

# Verifica che il PID nel lockfile è lo stesso del processo
```

### Ferma lo Scheduler

**Metodo 1: Da interfaccia web**
```
1. Clicca "⏹️ Ferma Scheduler"
2. Il punto diventa rosso (Arrestato)
```

**Metodo 2: Da terminale**
```bash
# Graceful shutdown
kill <PID>

# Force kill (last resort)
kill -9 <PID>
```

---

## 🧪 Test della Protezione

### Test 1: Verifica Lockfile Creato
```bash
cd ~/telegram-notion-scheduler

# Terminal 1: Avvia scheduler
python3 scheduler.py

# Terminal 2: Controlla lockfile
ls -la .scheduler.lock
cat .scheduler.lock

# Output dovrebbe mostrare il PID del processo
```

### Test 2: Verifica Protezione Duplicato
```bash
# Terminal 1: Scheduler già in esecuzione
python3 scheduler.py
# Output:
#   ✓ Lock acquired (PID: 14521)
#   ✓ Scheduler started successfully

# Terminal 2: Prova ad avviare un'altra istanza
python3 scheduler.py
# Output:
#   ✗ Scheduler already running (PID: 14521)
#   ✗    Only one instance allowed!
#   ✗    To stop it: kill 14521
#   ✗ Cannot start scheduler - another instance is already running!
```

### Test 3: Verifica Pulizia Lockfile
```bash
# Con scheduler in esecuzione
kill <PID>
sleep 2

# Lockfile dovrebbe essere automaticamente rimosso
ls -la .scheduler.lock
# Output: No such file or directory ✅
```

---

## 🔍 Diagnostica

### Problema: "Scheduler always shows Arrestato even though it's running"

**Soluzione:**

1. Verifica che il lockfile esista:
   ```bash
   cat .scheduler.lock
   ```
   Se non esiste, il lockfile non è stato creato (possibile errore di avvio)

2. Verifica che il PID nel lockfile sia vivo:
   ```bash
   PID=$(cat .scheduler.lock)
   ps -p $PID
   ```
   Se non esiste, processo morto ma lockfile non pulito

3. Verifica che il server stia controllando il lockfile:
   ```bash
   curl http://localhost:5555/api/status
   ```
   Dovrebbe ritornare `"running": true`

### Problema: "Lockfile remains even after killing scheduler"

**Causa:** `kill -9` termina immediatamente senza cleanup

**Soluzione:**
```bash
# Usa SIGTERM instead (graceful)
kill -15 <PID>
sleep 2

# Se ancora presente, manual cleanup
rm .scheduler.lock
```

### Problema: "Multiple instances started anyway"

**Possibile causa:** Vecchi lockfile con PID di processo morto

**Soluzione:**
```bash
# Pulisci lockfile manualmente
rm .scheduler.lock

# Verifica che nessun scheduler sia in esecuzione
pkill -f "python3 scheduler.py"

# Avvia nuovo scheduler
python3 scheduler.py
```

---

## 📊 Architettura Tecnica

### File Coinvolti

| File | Ruolo | Modifiche |
|------|-------|-----------|
| `scheduler.py` | Main scheduler | +`_acquire_lock()`, `_release_lock()`, signal handlers |
| `scheduler-server.py` | Web API backend | +`get_lockfile_pid()`, updated `is_scheduler_running()` |
| `scheduler-launcher.html` | Web UI | Aggiorna status ogni 10 sec |

### Funzioni Chiave

#### `scheduler.py::_acquire_lock()`
```python
- Controlla se LOCKFILE esiste
- Se esiste:
  - Leggi PID
  - Se PID è vivo → Rifiuta
  - Se PID è morto → Pulisci
- Crea LOCKFILE con PID attuale
- Ritorna True/False per successo
```

#### `scheduler-server.py::get_lockfile_pid()`
```python
- Leggi LOCKFILE se esiste
- Verifica che PID sia vivo con psutil
- Se morto → Rimuovi lockfile
- Ritorna PID o None
```

#### `scheduler-server.py::is_scheduler_running()`
```python
- Check 1: Lockfile con PID valido?      (PRIMARY)
- Check 2: Fallback a pgrep per running processes
- Ritorna True/False
```

---

## ⚙️ Configurazione

### Environment Variables
Non sono necessari. Il lockfile è gestito internamente.

### Timeout e Limiti
- **Lock check timeout:** Istantaneo
- **UI refresh interval:** 10 secondi
- **PID check:** Usa `psutil.pid_exists()` (fast)

---

## 📞 Troubleshooting Checklist

- [ ] Verifica che lockfile esista: `ls -la .scheduler.lock`
- [ ] Verifica che PID nel lockfile sia vivo: `ps -p $(cat .scheduler.lock)`
- [ ] Verifica che server veda il lockfile: `curl http://localhost:5555/api/status`
- [ ] Verifica che scheduler-server sia in esecuzione: `pgrep -f scheduler-server.py`
- [ ] Verifica che UI auto-refreshi ogni 10 sec (guarda timestamp)
- [ ] Se stuck, kill -9 tutto e restart manualmente

---

## 🎯 Benefici del Sistema

✅ **Semplicità:** Una sola istanza garantita
✅ **Robustezza:** Pulisce lockfile stantii automaticamente
✅ **Visibilità:** UI mostra chiaramente lo stato
✅ **Nessuna configurazione:** Funziona out-of-the-box
✅ **Performance:** Check istantanei (no timeouts)

---

## 🔗 Relazione con Altre Parti

### Relazione con Status Update Fix
- **Status Update Fix (FIXES_SUMMARY.md):** Risolve duplicati quando status non aggiorna
- **Lockfile Failsafe:** Previene che due istanze partano contemporaneamente
- **Insieme:** Sistema robusto che previene duplicati a due livelli

### Relazione con Timing
- **TIMING_AND_STATUS_GUIDE.md:** Spiega quando i post vengono pubblicati
- **Lockfile Failsafe:** Assicura che il checking avviene una volta al 15 minuti (non in parallelo)

---

**Data:** 2025-11-17
**Status:** ✅ IMPLEMENTATO E TESTATO
**Prossimi Passi:** Monitora con UI per 24h e conferma stabilità
