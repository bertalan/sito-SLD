# Studio Legale – SLD

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](CHANGELOG.md)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Security](https://img.shields.io/badge/security-pip--audit-green.svg)](requirements.txt)

Sito web professionale per Studio Legale, realizzato con Wagtail/Django, Docker (o senza) e frontend brutalista. Progettato per soddisfare esigenze di prenotazione, domiciliazioni, contatti, pagamenti online e presentazione delle aree di attività.

📚 **Documentazione**: [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md) | [UPGRADE.md](UPGRADE.md) | [CHANGELOG.md](CHANGELOG.md)

---

## ⚡ Quick Start - Prima Installazione

### 🐳 Con Docker (consigliato per sviluppo)

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
```

### 🐍 Senza Docker (consigliato per produzione)

```bash
# 1. Clona e configura
git clone https://github.com/bertalan/sito-SLD.git
cd sito-SLD
cp .env.example .env

# 2. Crea virtualenv e installa dipendenze
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# oppure: venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Configura database PostgreSQL
# Crea database e utente, poi modifica .env con le credenziali

# 4. Migrazioni e dati demo
python manage.py migrate
python manage.py createsuperuser
python manage.py setup_demo_data

# 5. Avvia server di sviluppo
python manage.py runserver

# 6. Accedi
# Sito: http://localhost:8000
# Admin: http://localhost:8000/admin/
```

> 💡 **Per deploy in produzione** senza Docker, usa lo script [`scripts/1_install.sh`](scripts/1_install.sh) che automatizza l'installazione su server con Nginx + Gunicorn.

---

### 📦 Cosa crea `setup_demo_data`
- ✅ **SiteSettings** con dati studio configurabili
- ✅ **HomePage** con testi hero
- ✅ **8 Aree di attività** (Penale, Famiglia, Civile, Lavoro, Amministrativo, Consumatori, Recupero Crediti, Mediazione)
- ✅ **Pagina Contatti** con form
- ✅ **Pagina Domiciliazioni** per colleghi avvocati
- ✅ **Pagina Articoli** con indice e 8 articoli demo (guide legali, novità normative, sentenze)
- ✅ **3 Categorie articoli** (Guide Legali, Novità Normative, Sentenze e Commenti)
- ✅ **Regole disponibilità** (Lun-Ven 9-13, 15-18)
- ✅ **2 Appuntamenti demo** (date relative: sempre nel futuro prossimo)
- ✅ **2 Domiciliazioni demo** (date relative: sempre attuali)

### 📅 Festività Italiane (opzionale)

```bash
# Con Docker:
docker compose exec web python manage.py setup_holidays  # default per 2 anni
docker compose exec web python manage.py setup_holidays --years 5

# Senza Docker:
python manage.py setup_holidays # default per 2 anni
python manage.py setup_holidays --years 5

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
- Integrazione **Stripe** (carte di credito) e **PayPal** (API REST v2)
- **Modalità pagamento flessibile**: ogni provider può essere `sandbox`, `live` o `off`
- **Pagamento differito**: se entrambi i provider sono `off`, il cliente può "Richiedere appuntamento" via email
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
- **Reinvio email da Wagtail**: bulk action "📧 Reinvia email" per reinviare conferme

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

### ♿ Widget Accessibilità WCAG 2.0
- Conforme a **WCAG 2.0 AA** e **Legge Stanca** (D.Lgs. 33/2013)
- **Controlli disponibili**:
  - Dimensione testo (80%-200%)
  - Modalità contrasto: Normale, Alto, Invertito
  - Evidenzia link
  - Focus potenziato
  - Blocca animazioni
  - Modalità lettura
  - Cursore grande
- **Posizionamento dinamico**:
  - Si sposta automaticamente sopra il cookie banner
  - Responsive per mobile/tablet/desktop
  - Non interferisce con la Wagtail userbar
- **Pulsante Reset (R)**: resetta tutte le preferenze (accessibilità + cookie)
- Preferenze salvate in localStorage

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
- **Badge stato regole**: colori verde/grigio per regole attive/disabilitate
- **Allineamento calendario**: verifica sincronizzazione Google Calendar
- **Cancellazione appuntamenti orfani**: rimozione sicura con conferma
- **Slot count modificabile**: gestione durata appuntamento in admin

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| CMS | Wagtail 6.4.1 |
| Backend | Django 5.2.9 |
| Database | PostgreSQL 15 |
| Frontend | Tailwind CSS (CDN) |
| Icone | Lucide |
| Mappe | Leaflet.js + OpenStreetMap |
| Pagamenti | Stripe, PayPal (API REST v2) |
| Videochiamate | Jitsi Meet |
| Container | Docker + Docker Compose |
| Server WSGI | Gunicorn |
| Static files | WhiteNoise |

## 🔒 Sicurezza

### Vulnerabilità CVE
Il progetto viene regolarmente scansionato con `pip-audit`:

```bash
# Con Docker:
docker compose exec web pip-audit

# Senza Docker (con venv attivo):
pip-audit

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
# Con Docker:
docker compose exec web python -m pytest sld_project/security_tests/ -v

# Senza Docker (con venv attivo):
python -m pytest sld_project/security_tests/ -v

# 28 test di sicurezza
```

## Test e TDD

Il progetto segue il metodo TDD (Test Driven Development):

- **Pytest + pytest-django**: tutti i moduli hanno test automatici
- **180+ test E2E** + **~115 test unit** su modelli, viste, pagine, pagamenti, email, iCal, SEO, GDPR, sicurezza
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
# Test unitari - Con Docker:
docker compose exec web python -m pytest tests/unit/ -v

# Test unitari - Senza Docker (con venv attivo):
python -m pytest tests/unit/ -v

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
- ✅ **29 test PaymentConfig e ResendEmailBulkAction**
- ✅ **28 test sicurezza** (headers, rate limit, file validation, secrets)

## Configurazione

### Variabili d'ambiente (.env) - Configurazione server e pagamenti

```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:pass@host:5432/dbname
POSTGRES_PASSWORD=your-db-password

# Pagamenti
PAYMENT_MODE=sandbox

# Stripe (sandbox | live | off)
STRIPE_MODE=sandbox
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# PayPal (sandbox | live | off)
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx

# Google Calendar (opzionale)
GOOGLE_CALENDAR_ICAL_URL=https://calendar.google.com/calendar/ical/xxx/basic.ics
```

### SiteSettings (Admin Wagtail) - Dati studio e contenuti

Vai su: **Admin → Impostazioni → Impostazioni Studio**

| Sezione | Configurazioni |
|---------|----------------|
| 📋 Identità Studio | Nome studio, avvocato |
| 📞 Contatti | Email, PEC, telefono, cellulare |
| 📍 Sede | Indirizzo, città, coordinate mappa |
| 🌐 Web & Social | Sito, Facebook, Twitter, LinkedIn |
| 💳 Prenotazioni | Durata slot, prezzo consulenza |
| 📧 Email SMTP | Server, porta, credenziali |
| 📊 Analytics | Google Analytics 4, Matomo |
| 📅 Google Calendar | Cache TTL |
| 📹 Videochiamate | Prefisso stanze Jitsi |
| 📄 Pagine Legali | Privacy Policy, Termini e Condizioni |

> ℹ️ Le **chiavi API pagamento** (Stripe/PayPal) vanno **solo in `.env`**, non in SiteSettings.


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

### 🚀 Script di Deploy e Verifica

La cartella `scripts/` contiene strumenti per il deploy e il monitoraggio:

| Script | Uso | Dove eseguirlo |
|--------|-----|----------------|
| [`1_install.sh`](scripts/1_install.sh) | Primo setup su server | Sul server (qualsiasi cartella) |
| [`2_verifiche.sh`](scripts/2_verifiche.sh) | Verifica salute sito | Ovunque (anche in locale) |

```bash
# 1. Primo deploy (sul server, come root, da qualsiasi cartella)
#    Lo script installa in APP_DIR configurato, non nella directory corrente
sudo bash scripts/1_install.sh

# 2. Verifica produzione (da qualsiasi macchina con accesso internet)
#    Verifica il DOMAIN configurato via HTTP
bash scripts/2_verifiche.sh
```

> 📖 Vedi [scripts/README.md](scripts/README.md) per documentazione dettagliata.

### Deploy manuale con Docker

```sh
# Collect static
docker compose exec web python manage.py collectstatic --noinput

# Run with gunicorn (dentro container)
docker compose exec web gunicorn sld_project.wsgi:application -c gunicorn.conf.py
```

### Deploy manuale senza Docker

Il progetto include:
- `gunicorn.conf.py` configurato per produzione
- `whitenoise` per static files
- Supporto proxy Nginx (X-Forwarded headers)

```sh
# Con virtualenv attivo
source venv/bin/activate

# Collect static
python manage.py collectstatic --noinput

# Run with gunicorn
gunicorn sld_project.wsgi:application -c gunicorn.conf.py
```

> 💡 **Consigliato**: Usa [`scripts/1_install.sh`](scripts/1_install.sh) per automatizzare il setup completo con Nginx + Gunicorn come servizio systemd.

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

## 📄 Licenza

Questo progetto è rilasciato sotto licenza [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

Sei libero di:
- **Condividere** — copiare e ridistribuire il materiale in qualsiasi mezzo o formato
- **Adattare** — remixare, trasformare e costruire sul materiale per qualsiasi scopo, anche commerciale

A condizione di dare **attribuzione** appropriata, fornire un link alla licenza e indicare se sono state apportate modifiche.

---

📄 **Per la personalizzazione avanzata**, consulta [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md)

Sviluppato con ❤️ e Copilot