# Changelog

Tutte le modifiche significative a questo progetto sono documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).

## [1.2.0] - 2026-01-03

### ✨ Nuove Funzionalità
- **Admin AvailabilityRule**: colonna "Stato" con badge colorati (verde attiva, grigio disabilitata)
- **Admin Allineamento Calendario**: nuova pagina per verificare sincronizzazione Google Calendar/appuntamenti
- **Cancellazione sicura appuntamenti orfani**: rimozione con conferma degli appuntamenti non più in Google Calendar

### ♿ Accessibilità
- **Widget accessibilità**: pulsanti rialzati di 20px (da bottom-24 a bottom-[116px])
- **Reset emergenza**: cambiato da doppio click a singolo click con conferma dialog

### 🧪 Test
- **Riorganizzazione struttura test**: unificata in `tests/unit/` e `tests/e2e/`
- **Nuovi test contact** (`tests/unit/contact/test_models.py`):
  - Validazione email standard e PEC
  - Gestione email unicode/IDN
  - Test modelli ContactPage, SocialLink, ContactFormField
- **Nuovi test SiteSettings** (`tests/unit/sld_project/test_settings.py`):
  - Validazione coordinate lat/lng (range, precisione, formato italiano)
  - Test campi obbligatori e singleton
- **180 test E2E** tutti passanti (accessibilità, cookie banner, interazioni complete)
- **86 test unitari** organizzati per modulo

---

## [1.1.0] - 2026-01-03

### 🔒 Security
- **Django 5.2.9**: aggiornamento critico per CVE-2025-13372 (SQL Injection) e CVE-2025-64460 (DoS)
- **requests 2.32.4**: fix CVE-2024-47081 (leak credenziali .netrc)
- **pip 25.3**: fix CVE-2025-8869
- **pip-audit**: scansione CVE ora integrata nel workflow

### 🛡️ Security Hardening
- **28 test di sicurezza**: copertura completa di tutte le patch implementate
- **HTTP Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options in produzione
- **SECRET_KEY**: obbligatoriamente caricata da .env
- **ALLOWED_HOSTS**: configurabile da .env
- **Rate Limiting**: protezione form con django-ratelimit (10/min contatti, 5/min booking)
- **File Validation**: MIME type checking con python-magic
- **WAGTAILDOCS_SERVE_METHOD**: 'serve_view' per protezione documenti

### 🔄 Modifiche
- **Logo/Favicon**: migrati da Document a Image (supporto SVG nativo)
- **Template URL**: `.file.url` per Wagtail Image invece di `.url`

### 📦 Dipendenze Aggiornate
| Pacchetto | Versione Precedente | Nuova Versione |
|-----------|---------------------|----------------|
| Django    | 5.2.1               | 5.2.9          |
| requests  | 2.32.3              | 2.32.4         |

### ⚠️ Breaking Changes
- Logo e Favicon devono essere ricaricati come **Immagini** (non più Documenti)
- Dopo `migrate`, azzerare manualmente i campi se esistono dati:
  ```sql
  UPDATE sld_project_sitesettings SET logo_id = NULL, favicon_id = NULL;
  ```

---

## [1.0.1] - 2026-01-02

### 🐛 Bugfix
- **Navbar z-index**: corretto posizionamento navbar sopra mappa Leaflet (z-index 9998)
- **Email Footer protetta**: codifica Base64 anti-spam anche nel footer
- **Coordinate**: accettano virgola come separatore decimale (auto-conversione)

### 🔄 Modifiche
- **twitter_handle → x_url**: rinominato campo, ora URLField (URL completo profilo X)
- **Privacy/Terms in DB**: contenuto pagine legali ora editabile da SiteSettings
- **Icona X nel footer**: aggiornata da Twitter a X con logo ufficiale

### ✨ Nuovi Campi SiteSettings
- `favicon`: icona sito configurabile da admin
- `privacy_policy`: contenuto Privacy Policy (HTML con variabili)
- `terms_conditions`: contenuto Condizioni Generali (HTML con variabili)

### 📝 Variabili Pagine Legali
Supportate: `{{studio_name}}`, `{{lawyer_name}}`, `{{address}}`, `{{city}}`, `{{email}}`, `{{email_pec}}`, `{{phone}}`

---

## [1.0.0] - 2026-01-02

### ✨ Features
- **Sistema Prenotazioni**: calendario interattivo, slot 30 min, pagamento Stripe/PayPal
- **Domiciliazioni Legali**: form completo con upload documenti, notifiche email
- **8 Aree di Attività**: Penale, Famiglia, Civile, Lavoro, Amministrativo, Consumatori, Recupero Crediti, Mediazione
- **Videochiamate Jitsi**: link generati automaticamente per consulenze video
- **SiteSettings Centralizzato**: tutti i dati studio configurabili da admin Wagtail
- **Email Conferma**: con allegato iCal (.ics) per aggiunta a calendario
- **Cookie Banner GDPR**: conforme con gestione consensi
- **Analytics**: supporto Google Analytics 4 e Matomo
- **Festività Italiane**: comando `setup_holidays` per bloccare date automaticamente
- **Protezione Email**: codifica Base64 anti-scraping

### 🔧 Comandi
- `setup_demo_data`: crea dati demo completi (pagine, servizi, appuntamenti, domiciliazioni)
- `setup_holidays`: genera festività italiane come date bloccate

### 📦 Stack
- Django 5.2 + Wagtail 6.4
- PostgreSQL 15
- TailwindCSS (CDN)
- Docker + Docker Compose

### 📝 Documentazione
- README.md con Quick Start
- CUSTOMIZATION_GUIDE.md per personalizzazione
- 93 test automatici

---

## Versioning

- `MAJOR.MINOR.PATCH` (es: 1.2.3)
- **MAJOR**: breaking changes, richiede migrazione manuale
- **MINOR**: nuove feature, retrocompatibili
- **PATCH**: bugfix, aggiornamento sicuro
