# Changelog

Tutte le modifiche significative a questo progetto sono documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).

## [1.0.0] - 2026-01-02

### ✨ Features
- **Sistema Prenotazioni**: calendario interattivo, slot 30 min, pagamento Stripe/PayPal
- **Domiciliazioni Legali**: form completo con upload documenti, notifiche email
- **8 Aree di Pratica**: Penale, Famiglia, Civile, Lavoro, Amministrativo, Consumatori, Recupero Crediti, Mediazione
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
