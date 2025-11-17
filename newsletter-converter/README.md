# 📧 Brevo Newsletter Converter

Convertitore offline per newsletter - trasforma testo formattato in HTML pronto per Brevo.

## Caratteristiche

✅ **100% Offline** - Funziona localmente su Google Chrome
✅ **Supporto Markdown** - `**grassetto**`, `*corsivo*`, `[link](url)`
✅ **UTM Params Automatici** - Aggiunge automaticamente utm_source, utm_campaign, utm_medium
✅ **Versioni Multilingue** - Supporta testo italiano + inglese
✅ **Link su Immagini** - Rendi le immagini divisorie cliccabili
✅ **Link Checker** - Visualizza e verifica tutti i link generati

## Come usarlo

### Opzione 1: Desktop (più veloce)
1. Scarica `Newsletter-Converter.html`
2. Doppio click per aprirlo in Chrome
3. Salva nei preferiti con `Cmd + D`
4. Usa come applicazione locale!

### Opzione 2: Clonare da Git
```bash
git clone <repo-url>
cd newsletter-converter
open Newsletter-Converter.html
```

## Guida rapida

### Input
- **Nome Campagna** - Es: "Bundle Novembre 2025" (per UTM)
- **Saluto Iniziale** - Es: "Ciao" (opzionale)
- **Testo Italiano** - Il contenuto principale della newsletter
- **URL Immagine** - Immagine divisoria tra italiano e inglese (opzionale)
- **Link Immagine** - Rendi l'immagine cliccabile (opzionale)
- **Testo Inglese** - Versione in inglese (opzionale)

### Formattazione Supportata

| Sintassi | Risultato |
|----------|-----------|
| `**testo**` | **grassetto** |
| `*testo*` | *corsivo* |
| `[testo](url)` | link con testo |
| `https://url.com` | link automatico |
| Doppio invio | nuovo paragrafo |
| `[**bold**](url)` | link in grassetto |

## Output

1. Clicca "Genera HTML"
2. L'HTML viene generato nella sezione destra
3. Clicca "Copia HTML"
4. Incolla su Brevo → Editor HTML
5. Invia!

## Note Importanti

⚠️ **Primo caricamento**: Richiede internet per scaricare Tailwind CSS (poi funziona offline)
💾 **Dati**: Rimangono solo in memoria - se aggiorna la pagina tutto viene perso
🔗 **Link**: I link ricevono automaticamente i parametri UTM se è compilato "Nome Campagna"

## Footer Brevo

Se abiliti il footer, vengono inclusi automaticamente:
- `{{ update_profile }}` - Link per aggiornare preferenze
- `{{ unsubscribe }}` - Link per disiscriversi

(Questi placeholder funzionano direttamente in Brevo)

## Condivisione

Puoi condividere il file `.html` con i colleghi - non ha dipendenze eccetto Tailwind CSS (caricato da CDN).

## Storico Aggiornamenti

- **v1.0** - Rilascio iniziale con supporto multilingue e link su immagini
