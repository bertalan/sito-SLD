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
studio_name, lawyer_name
```

### 📞 Contatti
```python
email, email_pec, phone, mobile_phone
```

### 📍 Sede
```python
address, city, maps_lat, maps_lng, maps_url
```

### 🌐 Web & Social
```python
website, facebook_url, twitter_handle, linkedin_url
```

### 📹 Videochiamate
```python
jitsi_room_prefix
```

### 💳 Pagamenti
```python
payment_mode        # demo/sandbox/live
stripe_public_key, stripe_secret_key, stripe_webhook_secret
paypal_client_id, paypal_client_secret
booking_slot_duration, booking_price_cents
```

### 📧 Email SMTP
```python
email_host, email_port, email_use_tls
email_host_user, email_host_password, email_from_address
```

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
| Servizi | `services.ServicesIndexPage` | `aree-pratica` |
| Contatti | `contact.ContactPage` | `contatti` |
| Domiciliazioni | `domiciliazioni.DomiciliazioniPage` | `domiciliazioni` |

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
Crea: SiteSettings, HomePage, ServiceAreas(8), ServicesIndexPage, ContactPage, DomiciliazioniPage, AvailabilityRules

## Migrazioni

Una per app: `*/migrations/0001_initial.py`
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py makemigrations <app>
```

## File Chiave per Personalizzazione

| Cosa | File |
|------|------|
| Logo | `sld_project/static/images/dr_Logo.svg` |
| Footer | `sld_project/templates/includes/footer.html` |
| Nav | `sld_project/templates/includes/navigation.html` |
| Hero | `home/templates/home/home_page.html` |
| SEO | `home/templatetags/seo_tags.py` |
| Privacy/Terms | `sld_project/templates/pages/privacy.html`, `terms.html` |
| Colori | TailwindCSS: `brand-black`, `brand-white`, `brand-gray`, `brand-silver`, `brand-accent` |

## Icone

Lucide Icons via CDN. Nomi usati: `scale`, `users`, `file-contract`, `briefcase`, `landmark`, `shield-alt`, `coins`, `handshake`

## Comandi Utili

```bash
# Shell Django
docker compose exec web python manage.py shell

# Collectstatic
docker compose exec web python manage.py collectstatic --noinput

# Superuser
docker compose exec web python manage.py createsuperuser
```

## Note Importanti

1. **Mai hardcodare** dati studio nei template - usare SiteSettings
2. **mobile_phone** è opzionale, mostrare solo se compilato
3. **Email** sempre con `|b64encode` per anti-spam
4. I test devono passare: 93 test attesi
5. Admin: `/admin/` (Wagtail) e `/django-admin/` (Django)
6. **Solo DEBUG, SECRET_KEY, DATABASE_URL** vanno in `.env` - tutto il resto in SiteSettings
7. Ogni campo SiteSettings ha `help_text` con istruzioni (es: dove trovare chiavi Stripe)
