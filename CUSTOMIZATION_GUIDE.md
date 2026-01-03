# Guida Personalizzazione Sito Studio Legale

## Stack
- Django 5.2 + Wagtail CMS + TailwindCSS
- Docker: `docker compose up -d`
- Test: `docker compose exec web python manage.py test`

## ⚠️ Importante: Configurazione Centralizzata

**TUTTE le configurazioni sono in SiteSettings (database).**

Configura da: Admin → Impostazioni → Impostazioni Studio

## Architettura Dati Centralizzata

**SiteSettings** (`sld_project/models.py`) = unica fonte per tutti i dati:

### 📋 Identità Studio
```python
studio_name, lawyer_name, logo, favicon
```

> **logo**: immagine SVG/PNG caricata in Wagtail **Images** (non Documents)
> **favicon**: immagine ICO/PNG/SVG per l'icona del browser

### 📞 Contatti
```python
email, email_pec, phone, mobile_phone
```

### 📍 Sede
```python
address, city, maps_lat, maps_lng, maps_url
```

> **maps_lat/maps_lng**: coordinate come testo, accettano sia punto che virgola (es: `41,9028` → salvato come `41.9028`)

### 🌐 Web & Social
```python
website, facebook_url, x_url, linkedin_url
```

### 📹 Videochiamate
```python
jitsi_room_prefix
```

### 💳 Pagamenti (v1.2.0+)

> ⚠️ **Breaking Change v1.2.0**: Le chiavi pagamento sono state **rimosse da SiteSettings** e vanno configurate **solo in `.env`**.

**In SiteSettings** (Admin → Impostazioni → Impostazioni Studio):
```python
booking_slot_duration  # Durata slot in minuti (default: 30)
booking_price_cents    # Prezzo in centesimi (es: 6000 = €60)
```

**In `.env`**:
```bash
# Modalità globale
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
```

**Modalità flessibile**:
- Se `STRIPE_MODE=off`: pulsante Stripe nascosto
- Se `PAYPAL_MODE=off`: pulsante PayPal nascosto
- Se **entrambi** `off`: pagamento differito via email (pulsante "Richiedi appuntamento")

**PaymentConfig** (`booking/payment_config.py`):
```python
from booking.payment_config import PaymentConfig

config = PaymentConfig()
config.stripe_enabled     # True se STRIPE_MODE != 'off'
config.paypal_enabled     # True se PAYPAL_MODE != 'off'
config.payment_deferred   # True se entrambi disabilitati
config.stripe_mode        # 'sandbox', 'live', 'off'
config.paypal_mode        # 'sandbox', 'live', 'off'
```

**Context processor** (già configurato in settings):
```django
{# Nei template #}
{% if payment_config.stripe_enabled %}
  <button>Paga con Stripe</button>
{% endif %}
{% if payment_config.payment_deferred %}
  <button>Richiedi appuntamento</button>
{% endif %}
```

### 📧 Email SMTP
```python
email_host, email_port, email_use_tls
email_host_user, email_host_password, email_from_address
```

### 📜 Pagine Legali
```python
privacy_policy, terms_conditions
```

> Contenuto HTML per Privacy e Condizioni Generali. Supporta variabili:
> `{{studio_name}}`, `{{lawyer_name}}`, `{{address}}`, `{{city}}`, `{{email}}`, `{{email_pec}}`, `{{phone}}`

### 📊 Analytics
```python
ga4_measurement_id      # Google Analytics 4
matomo_url, matomo_site_id  # Matomo
```

### 📅 Google Calendar
```python
google_calendar_ical_url, google_calendar_cache_ttl
```

**Accesso nei template:**
```django
{{ settings.sld_project.SiteSettings.studio_name }}
{{ settings.sld_project.SiteSettings.email|b64encode }}  {# anti-spam #}
```

**Accesso in Python:**
```python
from sld_project.models import SiteSettings
settings = SiteSettings.get_current()
# oppure
settings.get_contact_dict()  # ritorna dict con tutti i campi
```

## Helper _get_studio_settings()

Presente in 4 file per email/iCal:
- `booking/email_service.py`
- `booking/ical.py`
- `domiciliazioni/ical.py`
- `domiciliazioni/views.py`

Pattern standard:
```python
def _get_studio_settings():
    try:
        from sld_project.models import SiteSettings
        s = SiteSettings.get_current()
        return {
            'name': s.lawyer_name,
            'studio_name': s.studio_name,
            'phone': s.phone,
            'mobile_phone': s.mobile_phone,
            'email': s.email,
            # ...altri campi
        }
    except:
        return {fallback values}
```

## Template Filter b64encode

`home/templatetags/seo_tags.py` - per offuscare email:
```python
@register.filter
def b64encode(value):
    return base64.b64encode(value.encode()).decode()
```

## Pagine Wagtail

| Pagina | Model | Slug |
|--------|-------|------|
| Home | `home.HomePage` | `home` |
| Servizi | `services.ServicesIndexPage` | `aree-attivita` |
| Contatti | `contact.ContactPage` | `contatti` |
| Domiciliazioni | `domiciliazioni.DomiciliazioniPage` | `domiciliazioni` || Articoli | `articles.ArticleIndexPage` | `articoli` |
## Domiciliazioni - Tribunali

`domiciliazioni/models.py` - TRIBUNALE_CHOICES:
```python
[('roma', 'Tribunale di Roma'),
 ('corte_appello', "Corte d'Appello di Roma"),
 ('gdp', 'Giudice di Pace di Roma'),
 ('tar', 'TAR Lazio'),
 ('unep', 'Ufficio UNEP di Roma')]
```

Indirizzi in `domiciliazioni/ical.py` - TRIBUNALI_INDIRIZZI

## Demo Data

```bash
docker compose exec web python manage.py setup_demo_data --force
```
Crea:
- SiteSettings con dati studio
- HomePage con testi hero
- 8 ServiceAreas (aree di attività)
- ServicesIndexPage, ContactPage, DomiciliazioniPage
- **ArticleIndexPage** con 8 articoli demo
- **3 Categorie articoli** (Guide Legali, Novità Normative, Sentenze e Commenti)
- AvailabilityRules (Lun-Ven 9-13, 15-18)
- **2 Appuntamenti demo** (date relative: domani e dopodomani lavorativi)
- **2 Domiciliazioni demo** (date relative: +3 e +5 giorni lavorativi)

### 📰 Articoli Demo

| Titolo | Categoria | Aree Collegate |
|--------|-----------|----------------|
| Guida in stato di ebbrezza | Guide Legali | Diritto Penale |
| Separazione consensuale | Guide Legali | Famiglia e Successioni |
| Ritardo consegna auto | Novità Normative | Consumatori, Civile |
| Licenziamento per giusta causa | Sentenze | Diritto Lavoro |
| Ricorso al TAR | Guide Legali | Amministrativo |
| Decreto ingiuntivo non pagato | Guide Legali | Recupero Crediti, Civile |
| Mediazione obbligatoria | Guide Legali | Mediazione |
| Eredità con debiti | Novità Normative | Famiglia e Successioni |

> Gli articoli hanno contenuti HTML completi (~500-800 parole) e date di pubblicazione scaglionate.

## Festività Italiane

Comando dedicato per bloccare le festività nel calendario prenotazioni:

```bash
# Festività per i prossimi 2 anni (default)
docker compose exec web python manage.py setup_holidays

# Per 5 anni
docker compose exec web python manage.py setup_holidays --years 5

# Escludi alcune festività
docker compose exec web python manage.py setup_holidays --exclude pasquetta ferragosto

# Solo alcune festività
docker compose exec web python manage.py setup_holidays --include-only natale pasqua

# Rimuovi e ricrea
docker compose exec web python manage.py setup_holidays --clear --years 3

# Lista festività disponibili
docker compose exec web python manage.py setup_holidays --list
```

Festività supportate: `capodanno`, `epifania`, `pasqua`, `pasquetta`, `liberazione`, `lavoro`, `repubblica`, `ferragosto`, `ognissanti`, `immacolata`, `natale`, `stefano`

> Pasqua e Pasquetta sono calcolate automaticamente (date mobili).

## Migrazioni

Una per app: `*/migrations/0001_initial.py`
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py makemigrations <app>
```

## File Chiave per Personalizzazione

| Cosa | File |
|------|------|
| Logo | `sld_project/static/images/StudioLegale.svg` |
| Footer | `sld_project/templates/includes/footer.html` |
| Nav | `sld_project/templates/includes/navigation.html` |
| Hero | `home/templates/home/home_page.html` |
| SEO | `home/templatetags/seo_tags.py` |
| Privacy/Terms | SiteSettings → `privacy_policy`, `terms_conditions` (contenuto da DB) |
| Colori | TailwindCSS: `brand-black`, `brand-white`, `brand-gray`, `brand-silver`, `brand-accent` |

## Icone

Lucide Icons via CDN. Nomi usati: `scale`, `users`, `file-contract`, `briefcase`, `landmark`, `shield-alt`, `coins`, `handshake`

## Funzionalità Admin (v1.2.0+)

### 📧 Reinvio Email Appuntamenti
Da Wagtail Admin → Snippets → Appuntamenti:
1. Seleziona uno o più appuntamenti
2. Dal menu azioni, scegli **"📧 Reinvia email"**
3. Conferma nella pagina di riepilogo

### 🔄 Allineamento Google Calendar
Verifica sincronizzazione tra appuntamenti e Google Calendar:
- Admin → Prenotazioni → **Allineamento Calendario**
- Mostra appuntamenti orfani (non più in Calendar)
- Cancellazione sicura con conferma

### 📊 Badge Stato Regole Disponibilità
Le regole mostrano badge colorati:
- 🟢 **Verde**: regola attiva
- ⚪ **Grigio**: regola disabilitata

### ⏱️ Slot Count Modificabile
Campo `slot_count` ora editabile per gestire durata appuntamento (multipli di 30 min).

## Comandi Utili

```bash
# Shell Django
docker compose exec web python manage.py shell

# Collectstatic
docker compose exec web python manage.py collectstatic --noinput

# Superuser
docker compose exec web python manage.py createsuperuser
```

## Configurazione Produzione con Gunicorn

Per garantire che Django usi le impostazioni di produzione (DEBUG=False, sicurezza attiva), configura il servizio systemd:

### File: `/etc/systemd/system/gunicorn-studiolegale.service`

```ini
[Unit]
Description=Gunicorn daemon for Studio Legale
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/studiolegale
Environment="DJANGO_SETTINGS_MODULE=sld_project.settings.production"
ExecStart=/var/www/studiolegale/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/studiolegale/sld.sock \
    sld_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Applicare le modifiche

```bash
# Ricarica la configurazione systemd
sudo systemctl daemon-reload

# Riavvia il servizio
sudo systemctl restart gunicorn-studiolegale.service

# Verifica lo stato
sudo systemctl status gunicorn-studiolegale.service
```

### ⚠️ Importante

La variabile `DJANGO_SETTINGS_MODULE=sld_project.settings.production` è **essenziale** per:
- `DEBUG=False`
- Header di sicurezza HTTP attivi
- CSRF/CORS configurati per il dominio di produzione

## Pagine di Errore Personalizzate

Il sito include pagine di errore personalizzate per 403, 404 e 500:

| Codice | Template | Descrizione |
|--------|----------|-------------|
| 403 | `sld_project/templates/403.html` | Accesso negato/CSRF |
| 404 | `sld_project/templates/404.html` | Pagina non trovata |
| 500 | `sld_project/templates/500.html` | Errore del server |

Le pagine 403 e 500 includono un link mailto con informazioni diagnostiche automatiche (URL, timestamp, browser, ecc.) per facilitare la segnalazione degli errori.

## Note Importanti

1. **Mai hardcodare** dati studio nei template - usare SiteSettings
2. **mobile_phone** è opzionale, mostrare solo se compilato
3. **Email** sempre con `|b64encode` per anti-spam
4. I test devono passare: **~115 test unit** + **180 test E2E**
5. Admin: `/admin/` (Wagtail) e `/django-admin/` (Django)
6. **In `.env`**: DEBUG, SECRET_KEY, DATABASE_URL + **tutte le chiavi pagamento** (STRIPE_*, PAYPAL_*)
7. Ogni campo SiteSettings ha `help_text` con istruzioni (es: dove trovare chiavi Stripe)
8. **Produzione**: Assicurarsi che `DJANGO_SETTINGS_MODULE=sld_project.settings.production` sia configurato nel servizio Gunicorn
