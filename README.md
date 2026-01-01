# Studio Legale D'Onofrio – SLD

Sito web professionale per Studio Legale D'Onofrio, realizzato con Wagtail/Django, Docker e frontend brutalista. Progettato per soddisfare esigenze di prenotazione, domiciliazioni, contatti, pagamenti online e presentazione delle aree di pratica.

## Funzionalità principali

### 🗓️ Sistema di Prenotazione
- Slot da 30 minuti con calendario interattivo
- Navigazione mensile avanti/indietro
- Regole di disponibilità configurabili per giorno della settimana
- Blocco date specifiche (festività, ferie)
- Scelta modalità: **in presenza** o **videochiamata**
- Pagamento anticipato obbligatorio (€60)
- Integrazione **Stripe** (carte di credito) e **PayPal**
- Upload allegati (PDF, DOC, immagini - max 20MB)

### 📹 Videochiamate Jitsi
- Generazione automatica link Jitsi per consulenze video
- Codice anonimizzato (nessun dato personale nel link)
- Link incluso in email di conferma

### 📧 Email e Notifiche
- Email conferma cliente con allegato **iCal** (.ics)
- Email notifica studio con dettagli appuntamento
- Supporto HTML + plain text
- Link Google Maps alla sede

### 📋 Domiciliazioni Legali
- Form completo con dati studio, parte, controparte, causa
- Campi: numero RG, Tribunale, data udienza, giudice
- Upload documenti multipli
- Notifica email automatica allo studio

### 📍 Contatti
- Indirizzo studio (Lecce)
- Mappa interattiva **OpenStreetMap** con Leaflet.js
- Form contatto con invio email

### ⚖️ Aree di Pratica
- 12 aree tematiche con pagine dedicate
- Icone **Lucide** per ogni area
- Contenuti da brochure professionale
- Ordinamento personalizzabile

### 📄 Pagine Legali
- Condizioni Generali di Contratto (`/termini/`)
- Privacy Policy GDPR (`/privacy/`)

### 🍪 Cookie Banner GDPR
- Banner conforme al GDPR con 3 opzioni: Accetta, Rifiuta, Personalizza
- Gestione consenso cookie tecnici e analitici
- Preferenze salvate per 365 giorni
- Link alla Privacy Policy integrato

### 📊 Analytics (GA4 + Matomo)
- Supporto **Google Analytics 4** (GA4)
- Supporto **Matomo** (alternativa privacy-friendly)
- Possibilità di usare uno, entrambi o nessuno
- Caricamento condizionale basato sul consenso cookie
- Funzione `trackEvent()` unificata per entrambe le piattaforme

### 🔒 Protezione Anti-Scraping Email
- Email codificate in **Base64** nell'HTML sorgente
- Decodifica solo su interazione utente (hover/click)
- Bot vedono solo placeholder testuali
- Protezione su tutte le pagine pubbliche

### 🗺️ SEO & Indicizzazione
- **Sitemap XML** dinamica (`/sitemap.xml`) via Wagtail
- **robots.txt** dinamico (`/robots.txt`)
- Meta tag Open Graph e Twitter Card
- Canonical URL automatici

### 🎨 Design
- Stile **brutalista** moderno
- Palette: nero, bianco, grigio, magenta (#e91e63)
- Logo SVG custom
- Layout responsive mobile-first
- Font: tracking-tight, uppercase headings

### 🔧 Amministrazione
- Backend **Wagtail CMS** completo
- Menu admin raggruppati per sezione
- Gestione disponibilità e date bloccate
- Esportazione appuntamenti

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| CMS | Wagtail 6.4 |
| Backend | Django 5.2 |
| Database | PostgreSQL 15 |
| Frontend | Tailwind CSS (CDN) |
| Icone | Lucide |
| Mappe | Leaflet.js + OpenStreetMap |
| Pagamenti | Stripe, PayPal |
| Videochiamate | Jitsi Meet |
| Container | Docker + Docker Compose |
| Server WSGI | Gunicorn |
| Static files | WhiteNoise |

## Test e TDD

Il progetto segue il metodo TDD (Test Driven Development):

- **Pytest + pytest-django**: tutti i moduli hanno test automatici
- **93 test** su modelli, viste, pagine, pagamenti, email, iCal, SEO, GDPR
- **Esecuzione**:
  ```sh
  docker compose exec web python manage.py test
  ```

### Copertura test:
- ✅ Modelli Appointment, AvailabilityRule, BlockedDate
- ✅ API slot disponibili
- ✅ Pagamenti Stripe/PayPal
- ✅ Generazione iCal (presenza + video)
- ✅ Invio email conferma
- ✅ Videochiamate Jitsi
- ✅ Gestione slot duplicati
- ✅ Servizi e aree di pratica
- ✅ Sitemap XML e robots.txt
- ✅ Cookie banner GDPR
- ✅ Google Analytics 4 e Matomo
- ✅ Consenso privacy nei form

## Configurazione

### Variabili d'ambiente (.env)

```env
# Database
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# PayPal
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
PAYPAL_MODE=sandbox

# Studio (opzionale, hanno default)
STUDIO_NAME=Avv. 
STUDIO_ADDRESS=
STUDIO_PHONE=
STUDIO_EMAIL=
STUDIO_PEC=
STUDIO_WEBSITE=
STUDIO_MAPS_URL=https://maps.google.com/...

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Analytics (scegli uno o entrambi)
GA4_MEASUREMENT_ID=G-XXXXXXXXXX
MATOMO_URL=https://matomo.example.com
MATOMO_SITE_ID=1
```

## Avvio rapido

1. Clona la repo:
   ```sh
   git clone https://github.com/bertalan/sito-SLD.git
   cd sito-SLD
   ```

2. Copia e configura `.env`:
   ```sh
   cp .env.example .env
   # Modifica con le tue chiavi
   ```

3. Avvia Docker:
   ```sh
   docker compose up --build
   ```

4. Applica migrazioni e crea superuser:
   ```sh
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

5. Accedi:
   - Sito: [http://localhost:8000](http://localhost:8000)
   - Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)

## Struttura progetto

```
sito-SLD/
├── booking/           # Prenotazioni, pagamenti, email, iCal
├── contact/           # Pagina contatti, mappa
├── domiciliazioni/    # Form domiciliazioni legali
├── home/              # Homepage, modelli Wagtail
├── services/          # Aree di pratica
├── sld_project/       # Settings Django, templates base, URL
│   ├── settings/
│   ├── templates/
│   └── static/
├── docker-compose.yml
├── Dockerfile
├── gunicorn.conf.py
├── requirements.txt
└── manage.py
```

## Deploy Produzione

Il progetto include:
- `gunicorn.conf.py` configurato per produzione
- `whitenoise` per static files
- Supporto proxy Nginx (X-Forwarded headers)

```sh
# Collect static
docker compose exec web python manage.py collectstatic --noinput

# Run with gunicorn
gunicorn sld_project.wsgi:application -c gunicorn.conf.py
```

## Licenze

### Codice sorgente
Il codice di questo progetto è **proprietario** e riservato a Studio Legale D'Onofrio.

### Dipendenze open source

| Pacchetto | Licenza |
|-----------|---------|
| Django | BSD-3-Clause |
| Wagtail | BSD-3-Clause |
| PostgreSQL | PostgreSQL License |
| Tailwind CSS | MIT |
| Lucide Icons | ISC |
| Leaflet.js | BSD-2-Clause |
| OpenStreetMap | ODbL |
| Jitsi Meet | Apache-2.0 |
| Stripe SDK | MIT |
| PayPal SDK | Apache-2.0 |
| Gunicorn | MIT |
| WhiteNoise | MIT |
| Pillow | HPND |
| pytest | MIT |

### Font e risorse
- Logo: design proprietario Studio Legale D'Onofrio

---

Sviluppato con ❤️ e Copilot per la trasformazione digitale dello studio legale.