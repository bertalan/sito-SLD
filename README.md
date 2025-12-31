# Studio Legale D'Onofrio – SLD

Sito web professionale per Studio Legale D'Onofrio, realizzato con Wagtail/Django, Docker e frontend brutalista. Progettato per soddisfare esigenze di prenotazione, domiciliazioni, contatti, pagamenti online e presentazione delle aree di pratica.

## Funzionalità principali

- **Prenotazione appuntamenti**: sistema con slot da 30 minuti, regole di disponibilità, blocco date, pagamento Stripe/PayPal.
- **Domiciliazioni**: form con upload documenti, gestione pratiche, notifica email.
- **Contatti**: form con mappa OpenStreetMap, invio email, doppio indirizzo studio.
- **Aree di pratica**: 12 aree, ciascuna con pagina dedicata, icona Lucide, contenuti brochure.
- **Admin Wagtail**: gestione pagine, aree, contenuti, media, utenti.
- **Design brutalista**: palette nero/grigio/magenta, logo custom, layout responsive.
- **Docker**: ambiente di sviluppo e produzione, Gunicorn/Nginx.

## Test e TDD

Il progetto segue il metodo TDD (Test Driven Development):

- **Pytest + pytest-django**: tutti i moduli hanno test automatici.
- **Copertura**: test su modelli, viste, pagine, pagamenti, link, navigazione, regole di prenotazione.
- **Esecuzione**:
  ```sh
  docker compose run --rm web python -m pytest -v
  ```
- **Test booking**: verifica slot, regole, pagamenti Stripe/PayPal, creazione/cancellazione appuntamenti.
- **Test navigation**: verifica accessibilità di tutte le pagine e link.
- **Test servizi**: verifica creazione e visualizzazione aree di pratica.

## Processi specifici

- **Prenotazione con pagamento**: scelta Stripe/PayPal, redirect automatico, conferma/cancellazione.
- **Gestione aree di pratica**: creazione automatica da brochure, icone Lucide, ordinamento personalizzato.
- **Domiciliazioni**: upload file, notifica email, gestione pratiche.
- **Contatti**: doppio indirizzo, mappa interattiva, invio email.
- **Responsive**: layout ottimizzato per mobile e desktop, titoli e box adattivi.
- **Admin**: tutte le pagine e contenuti gestibili da backend Wagtail.

## Avvio rapido

1. Clona la repo:
   ```sh
   git clone https://github.com/bertalan/sito-SLD.git
   cd sito-SLD
   ```
2. Crea file `.env` con chiavi Stripe/PayPal:
   ```
   STRIPE_PUBLIC_KEY=pk_test_...
   STRIPE_SECRET_KEY=sk_test_...
   PAYPAL_CLIENT_ID=...
   PAYPAL_CLIENT_SECRET=...
   PAYPAL_MODE=sandbox
   ```
3. Avvia Docker:
   ```sh
   docker compose up --build
   ```
4. Accedi:
   - Sito: [http://localhost:8000](http://localhost:8000)
   - Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/) (user: admin/admin123)

## Struttura

- `booking/` – prenotazioni, pagamenti
- `domiciliazioni/` – form e gestione pratiche
- `contact/` – contatti, mappa
- `services/` – aree di pratica, pagine dedicate
- `home/` – homepage, hero, box aree
- `sld_project/` – settings, templates base
- `example-UI/` – prototipo frontend React/Vite

## Note
- Tutte le modifiche sono versionate su GitHub branch `main`.
- Per richieste, bug o nuove aree di pratica, apri una issue.

---
Copilot: progetto ottimizzato per test, automazione e gestione legale digitale.