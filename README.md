# WooCommerce → NocoDB Sync Script

Sincronizza automaticamente ordini e clienti da WooCommerce a NocoDB per automatizzare il customer care.

## 📋 Caratteristiche

- ✅ Sincronizzazione intelligente di clienti con aggregazione (conteggio ordini, totale speso)
- ✅ Sincronizzazione ordini con deduplicazione per stato
- ✅ Freeze automático di ordini "completed" e "cancelled" (non sincronizzati più)
- ✅ Logica di sync intelligente: ultimi 7 giorni + full sync una volta al giorno
- ✅ Logging dettagliato in `/tmp/wc-nocodb-sync.log`
- ✅ Error handling robusto con retry logic
- ✅ Rate limiting gentile per WooCommerce

## 🚀 Setup

### 1. Instalazione dipendenze

```bash
pip install requests python-dotenv
```

### 2. Configurazione

#### Opzione A: File JSON (consigliato per production)

Copia il template e inserisci i tuoi dati:

```bash
cp wc-nocodb-config.example.json ~/.wc-nocodb-sync.json
nano ~/.wc-nocodb-sync.json
```

Struttura del file:
```json
{
  "woocommerce": {
    "store_url": "https://your-store.com",
    "consumer_key": "ck_...",
    "consumer_secret": "cs_..."
  },
  "nocodb": {
    "api_url": "https://app.nocodb.com/api/v2",
    "api_token": "tZ_...",
    "table_ids": {
      "clienti": "REDACTED_TABLE_ID",
      "ordini": "REDACTED_TABLE_ID"
    }
  }
}
```

#### Opzione B: Variabili ambiente

```bash
cp .env.example .env
# Edita .env con i tuoi dati
nano .env
# Poi esporta
export $(cat .env | xargs)
```

### 3. Ottenere le credenziali

#### WooCommerce API
1. Vai in WordPress Admin → WooCommerce → Settings → Advanced → REST API
2. Crea una nuova chiave API
3. Copia `Consumer Key` e `Consumer Secret`

#### NocoDB
1. Vai in NocoDB → Account → Tokens
2. Crea un nuovo token API (non MCP)
3. Assicurati che abbia permessi di lettura/scrittura

## 📖 Utilizzo

### Esecuzione manuale

```bash
# Sync ultimi 7 giorni
python3 wc-nocodb-sync.py

# Full sync (tutti gli ordini)
python3 wc-nocodb-sync.py --full-sync

# Con config personalizzato
python3 wc-nocodb-sync.py -c /path/to/config.json

# Con logging debug
python3 wc-nocodb-sync.py --log-level DEBUG
```

### Setup cron job (sync una volta al giorno)

```bash
# Modifica crontab
crontab -e

# Aggiungi questa linea (ogni giorno alle 00:00 - mezzanotte)
0 0 * * * /usr/bin/python3 ~/.wc-nocodb-sync.py -c ~/.wc-nocodb-sync.json >> /tmp/wc-nocodb-sync-cron.log 2>&1
```

### Esecuzione manuale (quando ti serve)

Quando vuoi sincronizzare gli ordini subito (non aspettare il cron):

```bash
# Sync rapido (ultimi 7 giorni)
python3 ~/.wc-nocodb-sync.py -c ~/.wc-nocodb-sync.json

# Oppure alias per usare velocemente
alias sync-wc="python3 ~/.wc-nocodb-sync.py -c ~/.wc-nocodb-sync.json"
sync-wc  # Così esegui il sync
```

Aggiungi l'alias nel tuo `.zshrc` o `.bashrc`:
```bash
echo 'alias sync-wc="python3 ~/.wc-nocodb-sync.py -c ~/.wc-nocodb-sync.json"' >> ~/.zshrc
```

### Setup webhook (sync in tempo reale - opzionale)

Per sincronizzare gli ordini in tempo reale quando cambiano stato in WooCommerce:

1. In WooCommerce: Settings → Advanced → Webhooks
2. Crea un webhook per l'evento "Order updated"
3. URL: `https://make.com/webhook/...` (da configurare su Make.com)
4. Make.com esegue uno scenario che chiama: `python3 wc-nocodb-sync.py --full-sync`

## 📊 Struttura NocoDB

### Tabella Clienti (REDACTED_TABLE_ID)

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| Id | Autonumber | ID primario |
| Email | Email | Chiave di deduplicazione |
| Name | Text | Nome completo |
| Username | Text | Username (= email) |
| Phone (Billing) | Text | Telefono |
| Country / Region | Text | Paese |
| City | Text | Città |
| Postal Code | Text | CAP |
| Orders | Number | Conteggio ordini (aggregato) |
| Total Spend | Currency | Totale speso (aggregato) |
| Last Active | DateTime | Ultimo update |

### Tabella Ordini (REDACTED_TABLE_ID)

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| Id | Autonumber | ID primario |
| Order Number | Text | ID ordine WooCommerce |
| Order Status | SingleSelect | Stato (Processing, Pending, Completed, Cancelled) |
| Order Date | DateTime | Data creazione ordine |
| Order Total Amount | Currency | Importo totale |
| Item Name | Text | Nome prodotto/evento |
| Email (Billing) | Email | Email cliente |
| Phone (Billing) | Text | Telefono |
| Payment Method Title | Text | Metodo pagamento |
| Customer Note | Text | Note cliente |
| First Name (Billing) | Text | Nome |
| Last Name (Billing) | Text | Cognome |
| Country Code (Billing) | Text | Codice paese |
| City (Billing) | Text | Città |
| Address 1&2 (Billing) | Text | Indirizzo |
| Postcode (Billing) | Text | CAP |
| Item Cost | Currency | Costo articolo |
| Quantity (- Refund) | Number | Quantità |

## 🔄 Logica di Sincronizzazione

### Clienti
- **Chiave deduplicazione**: Email (lowercase)
- **INSERT**: Se email non esiste in NocoDB
- **UPDATE**: Se email esiste, aggiorna Orders e Total Spend
- **Aggregazione**: Count ordini + Sum importi da tutti gli ordini WC

### Ordini
- **Chiave deduplicazione**: Order Number (ID WooCommerce)
- **INSERT**: Se ordine non esiste in NocoDB
- **UPDATE**: Se ordine esiste E lo stato è cambiato (e non è frozen)
- **FREEZE**: Ordini con stato "Completed" o "Cancelled" non vengono più sincronizzati
- **Filtri**: Solo ordini con status "Processing", "Pending", "On-Hold" negli ultimi 7 giorni (o tutti se --full-sync)

## 📝 Logging

I log sono salvati in `/tmp/wc-nocodb-sync.log` con formato:
```
2025-11-11 14:25:30,123 - INFO - 🚀 Avviando sync WooCommerce → NocoDB
2025-11-11 14:25:31,456 - INFO - 📦 Trovati 47 ordini processing da WooCommerce
2025-11-11 14:25:35,789 - INFO - 👥 Clienti: 12 nuovi, 35 aggiornati
2025-11-11 14:25:38,012 - INFO - 📋 Ordini: 8 nuovi, 4 aggiornati
2025-11-11 14:25:40,345 - INFO - STATUS: ✅ OK
```

## ⚠️ Error Handling

- **WooCommerce rate limit**: Attende 5 secondi e riprova
- **NocoDB errore**: Logga errore ma continua con il prossimo record
- **Token non valido**: Esce con errore e suggerisce di rigenerare il token

## 🔐 Sicurezza

- **Non salvare credenziali nel codice**: Usa config.json con permessi 600 o variabili ambiente
- **Token limitati**: Usa token API con permessi minimi (lettura/scrittura tabelle)
- **SSL/TLS**: Tutte le API calls usano HTTPS

Esempio permessi config.json:
```bash
chmod 600 ~/.wc-nocodb-sync.json
```

## 🐛 Troubleshooting

### "Authentication required - Invalid token"
- Rigenera un nuovo token API in NocoDB
- Assicurati che il token abbia permessi di lettura/scrittura

### "Cannot GET /api/v2/tables/..."
- Verifica che i table IDs siano corretti
- I table IDs devono essere nel formato `REDACTED_TABLE_ID` (vedi NocoDB URL)

### Ordini non sincronizzati
- Controlla che lo stato sia uno di: "processing", "pending", "on-hold"
- Se ordine è "completed" o "cancelled", non verrà più sincronizzato (freeze logic)
- Verifica il log: `/tmp/wc-nocodb-sync.log`

### Rate limit WooCommerce
- Lo script attende automaticamente 5 secondi e riprova
- Se succede spesso, aumenta l'intervallo del cron job

## 📞 Support

Per problemi:
1. Controlla il log: `cat /tmp/wc-nocodb-sync.log`
2. Esegui con `--log-level DEBUG`: `python3 wc-nocodb-sync.py --log-level DEBUG`
3. Verifica le credenziali in wc-credentials.txt

## 📄 Licenza

MIT

---

**Ultimo update**: 2025-11-11
**Versione**: 1.0
**Status**: ✅ Production Ready
