# ⏰ Guida Tecnica: Timing e Status Update

## 📋 Sommario
- ✅ **Come funziona l'orario di "Uscita"**
- ✅ **Come funziona l'aggiornamento dello Status**
- ✅ **Come diagnosticare problemi**

---

## ⏰ Come Funziona l'Orario "Uscita"

### Logica di Filtraggio
Lo scheduler pubblica un post SOLO quando tutti questi criteri sono soddisfatti:

```python
✅ Status = "Programmato"
✅ Tipo = "Telegram_testo" OR "Telegram_poll"
✅ Uscita <= ORA ATTUALE (Roma timezone)
✅ Uscita >= TODAY (non più di 30 giorni nel futuro)
```

### Esempi Pratici

| Uscita | Ora Attuale | Pubblica? | Motivo |
|--------|------------|-----------|--------|
| 14:00 Roma | 14:01 Roma | ✅ SÌ | Orario passato |
| 14:00 Roma | 14:00 Roma | ✅ SÌ | Orario attuale |
| 14:00 Roma | 13:59 Roma | ❌ NO | Orario nel futuro |
| 2025-12-25 | 2025-11-17 | ❌ NO | Oltre +30 giorni |

### Timezone
Tutto è calcolato in **Rome timezone (Europe/Rome)**:
- Se il tuo Notion è in UTC, lo scheduler converte automaticamente
- Se specifichi solo una data (senza ora), assume fine giornata (23:59 Roma)

### Codice di Controllo
```python
# Da notion_handler.py linea 139
if publish_dt > current_time:
    logger.debug(f"Skipping post - Uscita ({publish_date_str}) is in the future")
    continue  # ← NON pubblica se è nel futuro
```

---

## 📝 Come Funziona l'Aggiornamento dello Status

### Flusso di Pubblicazione

```
1. Scheduler trova post con Status="Programmato"
                    ↓
2. Scheduler pubblica su Telegram
                    ↓
3. Aggiorna Status a "Pubblicato" in Notion
                    ↓
4. La prossima volta, il post NON viene più trovato
   (perché Status ≠ "Programmato")
```

### Cosa Succede Quando lo Status Viene Aggiornato

#### ✅ Successo: Post Pubblicato
```
Notion log:
  ✓ Updated post XYZ status to 'Pubblicato'

Scheduler log:
  ✓ Post published successfully: "TELEGRAM - PREMIER NC4000"
  ✓ Post 'TELEGRAM - PREMIER NC4000' marked as published in Notion
```

**Risultato in Notion:**
- Status cambia da "Programmato" → "Pubblicato" ✅
- Message ID viene salvato (se disponibile)
- Post NON verrà più ripubblicato

#### ❌ Fallimento: Post Non Pubblicato
```
Scheduler log:
  ✗ Failed to publish post: "TELEGRAM - PREMIER NC4000"
  ✓ Post 'TELEGRAM - PREMIER NC4000' marked as errored in Notion
```

**Risultato in Notion:**
- Status cambia da "Programmato" → "Errore" ✅
- Puoi leggere l'errore nei log
- Dopo aver risolto, puoi riportare lo Status a "Programmato"

#### ⚠️ Problema: Status Update Fallisce
```
Scheduler log:
  ✓ Post published successfully on Telegram
  ⚠️ Post published but status update failed

Notion:
  Status rimane "Programmato" ❌
```

**Pericolo:** Il post potrebbe essere ripubblicato!
**Soluzione:** Assicurati che il token Notion abbia permessi di scrittura

---

## 🔍 Come Diagnosticare Problemi

### Scenario 1: Post Non Si Pubblica

**Domanda:** Hai messo il post con Status="Programmato" ma non viene pubblicato?

**Checklist:**
```
1. ✅ Verifica Uscita
   - È nel passato? (rispetto a ora Roma)
   - È oggi o nei prossimi 30 giorni?

2. ✅ Verifica Status
   - È ESATTAMENTE "Programmato" (case-sensitive?)
   - Non è "programmato", "PROGRAMMATO", "Approvato", ecc

3. ✅ Verifica Tipo
   - È "Telegram_testo" o "Telegram_poll"?
   - Non è "Instagram_post", "Facebook_post", ecc

4. ✅ Verifica Messaggio
   - Il campo "Messaggio" ha contenuto?
   - Non è vuoto?

5. ✅ Controlla i Log
   bash check_scheduler.sh           # Verifica che sia in esecuzione
   tail -50 scheduler.log            # Leggi ultimi 50 log

   Cerca log che contengono il titolo del post:
   - Se vedi "Skipping post" → controlla il motivo
   - Se vedi "No scheduled posts" → nessun post matcha i criteri
```

### Scenario 2: Post Pubblicato Più Volte

**Domanda:** Il post è stato pubblicato 2+ volte su Telegram?

**Cause Possibili:**
1. ❌ Più istanze dello scheduler in esecuzione
2. ❌ Status non è stato aggiornato a "Pubblicato"

**Diagnosi:**
```bash
# Controlla istanze
ps aux | grep "python3 scheduler.py" | grep -v grep

# Se vedi più di 1 riga, hai duplicati!
# Soluzione:
pkill -9 -f "python3 scheduler.py"
# Riavvia una sola istanza
cd ~/telegram-notion-scheduler && source venv/bin/activate && python3 scheduler.py
```

**Oppure controlla i log:**
```bash
# Se vedi questo, lo status update ha fallito:
⚠️ Post published but status update failed

# Soluzione:
# 1. Vai a Notion e cambia Status manualmente a "Pubblicato"
# 2. Verifica che il token Notion abbia permessi di scrittura
```

### Scenario 3: Status Non Cambia a "Pubblicato"

**Domanda:** Il post si pubblica su Telegram ma Status rimane "Programmato"?

**Cause Possibili:**
1. ❌ Token Notion non ha permessi di **SCRITTURA**
2. ❌ Campo Status non è del tipo corretto ("status" vs "select")
3. ❌ API Notion non risponde

**Diagnosi:**
```bash
# Leggi i log per messaggi di errore
tail -100 scheduler.log | grep -i "status\|update"

# Cerca questi errori:
# "Failed to update post" → problema di permessi/API
# "Notion API returned 403" → permessi insufficienti
# "Timeout updating post" → API non risponde
```

**Soluzione:**
1. **Verifica permessi del token:**
   - Vai a Notion Settings → Integrations
   - Assicurati che l'integration abbia accesso alla tua database
   - Accertati che abbia permessi di "Update content"

2. **Verifica campo Status:**
   ```
   In Notion, il campo Status deve essere:
   - Nome: "Status"
   - Tipo: "Status" (non "Select")
   ```

3. **Testa manualmente:**
   ```bash
   python3 test_connection.py
   # Dovrebbe dire:
   # ✓ Notion connection successful
   # ✓ Telegram connection successful
   ```

---

## 📊 Flow Diagram

```
┌─────────────────────────────────────┐
│  Notion Database                    │
│  Status="Programmato"               │
│  Uscita=oggi o nel passato          │
│  Tipo="Telegram_testo"              │
└────────────────┬────────────────────┘
                 │
                 ↓ (ogni 15 minuti)
        ┌────────────────────┐
        │ Scheduler Checks   │
        │ (check_and_publish)│
        └────────┬───────────┘
                 │
        ┌────────▼────────────┐
        │ All Criteria Met?   │
        └─────┬──────┬────────┘
              │      │
        YES───┘      └─── NO → Skip post
              │
              ↓
        ┌──────────────────────────┐
        │ Publish to Telegram      │
        │ (telegram_handler)       │
        └──┬───────────────────┬───┘
           │                   │
       SUCCESS              FAILURE
           │                   │
           ↓                   ↓
    ┌─────────────────┐  ┌──────────────┐
    │ Update Status:  │  │Update Status:│
    │ "Pubblicato"    │  │  "Errore"    │
    └────────┬────────┘  └──────┬───────┘
             │                  │
             ↓                  ↓
    Status Updated in Notion   (problema risolto?)
    ↓
    Post NON verrà più ripubblicato ✅
```

---

## 🔧 Debugging Avanzato

### Attiva Verbose Logging
Modifica `scheduler.py`:
```python
logging.basicConfig(
    level="DEBUG"  # ← Cambia da INFO a DEBUG
)
```

Ora vedrai più dettagli:
```
DEBUG - Skipping post - Uscita (2025-11-20T10:00:00) is in the future
DEBUG - Updating page 2aef88ad-0121-80b4-849e-e89bae14f093 with status='Pubblicato'
```

### Testa Manualmente
```bash
# Crea un post test in Notion con:
# - Status = "Programmato"
# - Uscita = adesso (in Rome timezone)
# - Tipo = "Telegram_testo"
# - Messaggio = "Test message"

# Poi esegui lo scheduler una volta:
cd ~/telegram-notion-scheduler
source venv/bin/activate
python3 scheduler.py

# Nel log dovresti vedere:
# ✓ Post published successfully
# ✓ Updated post XYZ status to 'Pubblicato'
```

---

## 📞 Domande Frequenti

### D: Perché il mio post non si pubblica se Uscita è nel futuro?
**R:** È corretto! Lo scheduler pubblica SOLO quando Uscita ≤ ora attuale. Cambia Uscita a un'ora passata se vuoi pubblicare subito.

### D: Posso publishare a un orario specifico?
**R:** Sì! Metti Uscita all'orario desiderato. Lo scheduler lo pubblicherà quando quel'ora arriverà.

### D: Se ripubblico lo stesso Status="Programmato", il post si ripubblica?
**R:** Sì. Se lo Status rimane "Programmato" e Uscita è nel passato, il post viene ripubblicato ogni 15 minuti. Cambia Status a "Pubblicato" per evitare.

### D: Cosa succede se ci sono 2 scheduler in esecuzione?
**R:** C'è una protezione: il codice skippa i post già "Pubblicato". Ma è comunque meglio averne solo 1.

---

**Status:** ✅ Sistema completamente documentato e robusto
