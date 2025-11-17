# 📚 Guida: Come creare i Post su Notion

## Struttura Database Notion

Il tuo database DEVE avere questi campi **ESATTAMENTE CON QUESTI NOMI**:

| Campo | Tipo | Cosa Scrivere |
|-------|------|---------------|
| **Nome** | Title | Il titolo/nome del post |
| **Messaggio** | Rich Text | **Il contenuto che verrà pubblicato su Telegram** |
| **Tipo** | Select | `Telegram_testo` oppure `Telegram_poll` |
| **Uscita** | Date with time | Data e ora quando pubblicare (timezone: Roma) |
| **Status** | Select | `Programmato` (per nuovi post) |
| **Immagine URL** | URL | (opzionale) Link immagine |
| **Poll Domanda** | Text | (solo per poll) La domanda |
| **Poll Opzioni** | Text | (solo per poll) `["Opzione 1", "Opzione 2", ...]` |
| **Channel ID** | Text | (opzionale) @canale_alternativo |
| **Message ID** | Text | (auto - non toccare) |

---

## 📝 Esempio 1: POST DI TESTO

**Quello che vedi su Notion:**

```
Nome:                 "Primo Post"
Messaggio:            "Ciao a tutti! Questo è il mio primo post automatico."
Tipo:                 Telegram_testo
Uscita:               17 novembre 2025 - 15:30 (ora Roma)
Status:               Programmato
```

**Quello che vedrai su Telegram:**
```
Ciao a tutti! Questo è il mio primo post automatico.
```

---

## 🖼️ Esempio 2: POST CON IMMAGINE

**Quello che vedi su Notion:**

```
Nome:                 "Post con Foto"
Messaggio:            "Guarda questa foto bellissima! 📸"
Tipo:                 Telegram_testo
Immagine URL:         https://example.com/foto.jpg
Uscita:               17 novembre 2025 - 16:00 (ora Roma)
Status:               Programmato
```

**Quello che vedrai su Telegram:**
```
[IMMAGINE]
Guarda questa foto bellissima! 📸
```

---

## 🗳️ Esempio 3: POLL

**Quello che vedi su Notion:**

```
Nome:                 "Sondaggio Colori"
Messaggio:            (puoi lasciare vuoto)
Tipo:                 Telegram_poll
Poll Domanda:         "Qual è il tuo colore preferito?"
Poll Opzioni:         ["Rosso", "Blu", "Verde", "Giallo"]
Uscita:               17 novembre 2025 - 17:00 (ora Roma)
Status:               Programmato
```

**Quello che vedrai su Telegram:**
```
Qual è il tuo colore preferito?
[ ] Rosso
[ ] Blu
[ ] Verde
[ ] Giallo
```

---

## ⚙️ Filtri Automatici

Il sistema pubblicherà SOLO i post che hanno:

✅ **Status** = `Programmato`
✅ **Tipo** = `Telegram_testo` OPPURE `Telegram_poll`
✅ **Uscita** = data/ora attuale o nel passato (timezone: Roma)

Dopo la pubblicazione, lo stato cambierà automaticamente a `Pubblicato`.

---

## 🐛 Troubleshooting

### ❌ Il post non viene pubblicato
Controlla che:
1. **Status** sia esattamente `Programmato` (non "programmato", non "PROGRAMMATO")
2. **Tipo** sia esattamente `Telegram_testo` o `Telegram_poll`
3. **Uscita** sia nel passato o ora (considera la timezone di Roma)
4. **Messaggio** non sia vuoto (per post di testo)

### ❌ Messaggio vuoto su Telegram
- Controlla che il campo **Messaggio** abbia contenuto
- Assicurati di aver scritto il testo nel campo Rich Text giusto

### ❌ Immagine non appare
- Verifica che l'URL sia corretto (prova ad aprirlo nel browser)
- Assicurati che il **Tipo** sia `Telegram_testo` (per mostrare l'immagine)

### ❌ Poll non funziona
- Verifica che il **Tipo** sia esattamente `Telegram_poll`
- Poll Opzioni deve essere un JSON array: `["Opzione1", "Opzione2"]`
- Deve avere almeno 2 opzioni
- Massimo 10 opzioni

---

## 📋 Checklist Prima di Pubblicare

Prima di impostare lo stato a "Programmato":

- [ ] Ho scritto il titolo in "Nome"
- [ ] Ho scritto il messaggio in "Messaggio" (se non è un poll)
- [ ] Ho selezionato il **Tipo** corretto
- [ ] Ho impostato la **Uscita** (considera timezone Roma)
- [ ] Se è un'immagine, ho messo l'URL in "Immagine URL"
- [ ] Se è un poll, ho riempito "Poll Domanda" e "Poll Opzioni"
- [ ] Lo "Status" è impostato a "Programmato"

Quando tutto è pronto, il bot pubblicherà il post automaticamente! ✨
