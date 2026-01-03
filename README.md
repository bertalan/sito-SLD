# Studio Legale – SLD

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/security-pip--audit-green.svg)](requirements.txt)

Sito web professionale per Studio Legale, realizzato con Wagtail/Django, Docker e frontend brutalista. Progettato per soddisfare esigenze di prenotazione, domiciliazioni, contatti, pagamenti online e presentazione delle aree di attività.

📚 **Documentazione**: [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md) | [UPGRADE.md](UPGRADE.md) | [CHANGELOG.md](CHANGELOG.md)

---

## ⚡ Quick Start - Prima Installazione

```bash
# 1. Clona e configura
git clone https://github.com/bertalan/sito-SLD.git
cd sito-SLD
cp .env.example .env

# 2. Avvia Docker
docker compose up --build -d

# 3. Migrazioni e dati demo
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py setup_demo_data

# 4. Accedi
# Sito: http://localhost:8000
# Admin: http://localhost:8000/admin/
# user: admin - password: admin
# CAMBIA LA PASSWORD
```

Il comando `setup_demo_data` crea:
- ✅ **SiteSettings** con dati studio configurabili
- ✅ **HomePage** con testi hero
- ✅ **8 Aree di attività** (Penale, Famiglia, Civile, Lavoro, Amministrativo, Consumatori, Recupero Crediti, Mediazione)
- ✅ **Pagina Contatti** con form
- ✅ **Pagina Domiciliazioni** per colleghi avvocati
- ✅ **Regole disponibilità** (Lun-Ven 9-13, 15-18)
- ✅ **2 Appuntamenti demo** (date relative: sempre nel futuro prossimo)
- ✅ **2 Domiciliazioni demo** (date relative: sempre attuali)

### 📅 Festività Italiane (opzionale)

```bash
# Genera festività per i prossimi 2 anni
docker compose exec web python manage.py setup_holidays

# Per 5 anni
docker compose exec web python manage.py setup_holidays --years 5

# Lista festività disponibili
docker compose exec web python manage.py setup_holidays --list
```

👉 **Personalizza i dati** da: Admin → Impostazioni → Impostazioni Studio

---

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
- Indirizzo studio (Roma)
- Mappa interattiva **OpenStreetMap** con Leaflet.js
- Form contatto con invio email

### ⚖️ Aree di Attività
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
| CMS | Wagtail 6.4.1 |
| Backend | Django 5.2.9 |
| Database | PostgreSQL 15 |
| Frontend | Tailwind CSS (CDN) |
| Icone | Lucide |
| Mappe | Leaflet.js + OpenStreetMap |
| Pagamenti | Stripe, PayPal |
| Videochiamate | Jitsi Meet |
| Container | Docker + Docker Compose |
| Server WSGI | Gunicorn |
| Static files | WhiteNoise |

## 🔒 Sicurezza

### Vulnerabilità CVE
Il progetto viene regolarmente scansionato con `pip-audit`:

```bash
docker compose exec web pip-audit
# Expected: "No known vulnerabilities found"
```

### Misure implementate
- ✅ **HTTP Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- ✅ **Rate Limiting**: protezione form con django-ratelimit
- ✅ **File Validation**: MIME type checking con python-magic
- ✅ **Secret Management**: SECRET_KEY e API keys in .env (mai in codice)
- ✅ **WAGTAILDOCS_SERVE_METHOD**: 'serve_view' per protezione documenti

### Test di sicurezza
```bash
docker compose exec web python -m pytest sld_project/security_tests/ -v
# 28 test di sicurezza
```

## Test e TDD

Il progetto segue il metodo TDD (Test Driven Development):

- **Pytest + pytest-django**: tutti i moduli hanno test automatici
- **180+ test E2E** + **86 test unit** su modelli, viste, pagine, pagamenti, email, iCal, SEO, GDPR, sicurezza
- **Struttura test unificata**:
  ```
  tests/
  ├── unit/           # Test unitari Django
  │   ├── booking/    # Modelli, viste, pagamenti, email
  │   ├── contact/    # Form contatti, validazione email
  │   ├── home/       # SEO tags, JSON-LD
  │   └── sld_project/ # SiteSettings, coordinate
  └── e2e/            # Test end-to-end Playwright
      ├── test_accessibility_widget.py
      ├── test_cookie_banner.py
      └── test_complete_interactions.py
  ```

### Esecuzione test:
```sh
# Test unitari
docker compose exec web python -m pytest tests/unit/ -v

# Test E2E (localmente, con Playwright installato)
cd tests/e2e && pytest -v -n 4
```

### Copertura test:
- ✅ Modelli Appointment, AvailabilityRule, BlockedDate
- ✅ API slot disponibili
- ✅ Pagamenti Stripe/PayPal
- ✅ Generazione iCal (presenza + video)
- ✅ Invio email conferma
- ✅ Videochiamate Jitsi
- ✅ Gestione slot duplicati
- ✅ Servizi e aree di attività
- ✅ Sitemap XML e robots.txt
- ✅ Cookie banner GDPR (E2E su 6 viewport)
- ✅ Widget accessibilità WCAG 2.0 (E2E su 6 viewport)
- ✅ Google Analytics 4 e Matomo
- ✅ Consenso privacy nei form
- ✅ Validazione email e PEC
- ✅ Validazione coordinate geografiche lat/lng
- ✅ **28 test sicurezza** (headers, rate limit, file validation, secrets)

## Configurazione

### Variabili d'ambiente (.env) - Solo configurazione server

```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:pass@host:5432/dbname
POSTGRES_PASSWORD=your-db-password
```

### SiteSettings (Admin Wagtail) - Tutte le altre configurazioni

Vai su: **Admin → Impostazioni → Impostazioni Studio**

| Sezione | Configurazioni |
|---------|----------------|
| 📋 Identità Studio | Nome studio, avvocato |
| 📞 Contatti | Email, PEC, telefono, cellulare |
| 📍 Sede | Indirizzo, città, coordinate mappa |
| 🌐 Web & Social | Sito, Facebook, Twitter, LinkedIn |
| 💳 Prenotazioni | Modalità pagamento, durata slot, prezzo |
| 💳 Stripe | Chiavi API pubbliche e segrete |
| 💳 PayPal | Client ID e Secret |
| 📧 Email SMTP | Server, porta, credenziali |
| 📊 Analytics | Google Analytics 4, Matomo |
| 📅 Google Calendar | URL iCal per sincronizzazione |
| 📹 Videochiamate | Prefisso stanze Jitsi |

> ℹ️ Ogni campo ha un **help text** con istruzioni su dove trovare i valori necessari.


## Struttura progetto

```
sito-SLD/
├── booking/           # Prenotazioni, pagamenti, email, iCal
├── contact/           # Pagina contatti, mappa
├── domiciliazioni/    # Form domiciliazioni legali
├── home/              # Homepage, modelli Wagtail
├── services/          # Aree di attività
├── sld_project/       # Settings Django, templates base, URL
│   ├── settings/
│   ├── templates/
│   └── static/
├── tests/             # Test suite unificata
│   ├── unit/          # Test unitari per modulo
│   │   ├── booking/
│   │   ├── contact/
│   │   ├── home/
│   │   └── sld_project/
│   └── e2e/           # Test E2E Playwright
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

### Licenze

#### Codice sorgente
Il codice di questo progetto è rilasciato come template riutilizzabile per studi legali.

#### Dipendenze open source

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

#### Font e risorse
- Logo: SVG personalizzabile in `sld_project/static/images/StudioLegale.svg`

---

📄 **Per la personalizzazione avanzata**, consulta [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md)

Sviluppato con ❤️ e Copilot