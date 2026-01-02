"""
Generatore file iCal per appuntamenti.
"""
from datetime import datetime, timedelta
from django.conf import settings
import hashlib


def _get_studio_settings():
    """Recupera le impostazioni studio da SiteSettings o fallback su settings.py."""
    try:
        from sld_project.models import SiteSettings
        site_settings = SiteSettings.get_current()
        return {
            'name': site_settings.lawyer_name or settings.STUDIO_NAME,
            'studio_name': site_settings.studio_name or "Studio Legale",
            'address': site_settings.address or settings.STUDIO_ADDRESS,
            'phone': site_settings.phone or settings.STUDIO_PHONE,
            'mobile_phone': site_settings.mobile_phone or '',
            'email': site_settings.email or settings.STUDIO_EMAIL,
            'website': site_settings.website or settings.STUDIO_WEBSITE,
            'maps_url': site_settings.maps_url or settings.STUDIO_MAPS_URL,
        }
    except Exception:
        return {
            'name': settings.STUDIO_NAME,
            'studio_name': "Studio Legale",
            'address': settings.STUDIO_ADDRESS,
            'phone': settings.STUDIO_PHONE,
            'mobile_phone': '',
            'email': settings.STUDIO_EMAIL,
            'website': settings.STUDIO_WEBSITE,
            'maps_url': settings.STUDIO_MAPS_URL,
        }


def generate_ical(appointment):
    """
    Genera un file iCal (.ics) per l'appuntamento.
    Include reminder 1h prima e tutti i dettagli necessari.
    """
    studio = _get_studio_settings()
    
    # Combina data e ora, usa la durata dinamica dell'appuntamento
    start_dt = datetime.combine(appointment.date, appointment.time)
    end_dt = start_dt + timedelta(minutes=appointment.duration_minutes)
    
    # Formatta per iCal (formato: YYYYMMDDTHHMMSS)
    def format_datetime(dt):
        return dt.strftime('%Y%m%dT%H%M%S')
    
    # UID univoco per l'evento
    uid = hashlib.sha256(f"{appointment.id}-{appointment.date}-{appointment.time}".encode()).hexdigest()[:32]
    
    # Location e descrizione basate sul tipo di consulenza
    if appointment.consultation_type == 'video':
        location = f"Videochiamata Jitsi: {appointment.jitsi_url}"
        description = f"""Consulenza legale in videochiamata con {studio['name']}.

Link per la videochiamata:
{appointment.jitsi_url}

Clicca sul link qualche minuto prima dell'orario previsto.

Per informazioni:
Mobile: {studio['phone']}
Email: {studio['email']}"""
    else:
        location = f"{studio['studio_name']} - {studio['address']}"
        description = f"""Consulenza legale in presenza con {studio['name']}.

Indirizzo:
{studio['address']}

Come raggiungerci:
{studio['maps_url']}

Per informazioni:
Mobile: {studio['phone']}
Email: {studio['email']}"""
    
    # Note cliente se presenti
    notes_text = ""
    if appointment.notes:
        notes_text = f"\\n\\nNote del cliente:\\n{appointment.notes}"
    
    # Escape caratteri speciali per iCal
    def escape_ical(text):
        return text.replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
    
    # Timestamp creazione
    dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    
    ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//{studio['studio_name']}//Prenotazioni//IT
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}@{studio['website'].replace('www.', '')}
DTSTAMP:{dtstamp}
DTSTART:{format_datetime(start_dt)}
DTEND:{format_datetime(end_dt)}
SUMMARY:Consulenza legale - {studio['studio_name']}
LOCATION:{escape_ical(location)}
DESCRIPTION:{escape_ical(description + notes_text)}
ORGANIZER;CN={studio['studio_name']}:mailto:{studio['email']}
ATTENDEE;CN={escape_ical(appointment.first_name)} {escape_ical(appointment.last_name)};RSVP=TRUE:mailto:{appointment.email}
STATUS:CONFIRMED
TRANSP:OPAQUE
BEGIN:VALARM
TRIGGER:-PT1H
ACTION:DISPLAY
DESCRIPTION:Promemoria: Consulenza legale tra 1 ora
END:VALARM
BEGIN:VALARM
TRIGGER:-PT1H
ACTION:EMAIL
SUMMARY:Promemoria: Consulenza legale tra 1 ora
DESCRIPTION:La tua consulenza con {studio['studio_name']} inizierà tra 1 ora.
ATTENDEE:mailto:{appointment.email}
END:VALARM
END:VEVENT
END:VCALENDAR"""
    
    return ical_content.strip()


def generate_ical_filename(appointment):
    """Genera il nome del file iCal."""
    date_str = appointment.date.strftime('%Y%m%d')
    time_str = appointment.time.strftime('%H%M')
    return f"appuntamento-studio-studiolegaledemo-{date_str}-{time_str}.ics"
