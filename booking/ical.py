"""
Generatore file iCal per appuntamenti.
"""
from datetime import datetime, timedelta
from django.conf import settings
import hashlib


def generate_ical(appointment):
    """
    Genera un file iCal (.ics) per l'appuntamento.
    Include reminder 1h prima e tutti i dettagli necessari.
    """
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
        description = f"""Consulenza legale in videochiamata con {settings.STUDIO_NAME}.

Link per la videochiamata:
{appointment.jitsi_url}

Clicca sul link qualche minuto prima dell'orario previsto.

Per informazioni:
Mobile: {settings.STUDIO_PHONE}
Email: {settings.STUDIO_EMAIL}"""
    else:
        location = f"Studio Legale - {settings.STUDIO_ADDRESS}"
        description = f"""Consulenza legale in presenza con {settings.STUDIO_NAME}.

Indirizzo:
{settings.STUDIO_ADDRESS}

Come raggiungerci:
{settings.STUDIO_MAPS_URL}

Per informazioni:
Mobile: {settings.STUDIO_PHONE}
Email: {settings.STUDIO_EMAIL}"""
    
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
PRODID:-//Studio Legale//Prenotazioni//IT
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}@example.com
DTSTAMP:{dtstamp}
DTSTART:{format_datetime(start_dt)}
DTEND:{format_datetime(end_dt)}
SUMMARY:Consulenza legale - Studio Legale
LOCATION:{escape_ical(location)}
DESCRIPTION:{escape_ical(description + notes_text)}
ORGANIZER;CN=Studio Legale:mailto:info@example.com
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
DESCRIPTION:La tua consulenza con lo Studio Legale inizierà tra 1 ora.
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
