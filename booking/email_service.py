"""
Servizio email per invio conferme prenotazione con allegato iCal.
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .ical import generate_ical, generate_ical_filename

logger = logging.getLogger(__name__)

# Traduzioni italiane per giorni e mesi
GIORNI_IT = {
    'Monday': 'Lunedì',
    'Tuesday': 'Martedì', 
    'Wednesday': 'Mercoledì',
    'Thursday': 'Giovedì',
    'Friday': 'Venerdì',
    'Saturday': 'Sabato',
    'Sunday': 'Domenica',
}

MESI_IT = {
    'January': 'Gennaio',
    'February': 'Febbraio',
    'March': 'Marzo',
    'April': 'Aprile',
    'May': 'Maggio',
    'June': 'Giugno',
    'July': 'Luglio',
    'August': 'Agosto',
    'September': 'Settembre',
    'October': 'Ottobre',
    'November': 'Novembre',
    'December': 'Dicembre',
}


def format_date_italian(date):
    """Formatta una data in italiano (es: Venerdì 23 Gennaio 2026)."""
    day_name = date.strftime('%A')
    month_name = date.strftime('%B')
    day_it = GIORNI_IT.get(day_name, day_name)
    month_it = MESI_IT.get(month_name, month_name)
    return f"{day_it} {date.day} {month_it} {date.year}"


def send_booking_confirmation(appointment):
    """
    Invia email di conferma al cliente e allo studio con allegato iCal.
    Ritorna un dict con lo stato di invio per ogni destinatario.
    """
    logger.info(f"Invio email conferma per appuntamento #{appointment.id} - {appointment.email}")
    
    # Genera il file iCal
    ical_content = generate_ical(appointment)
    ical_filename = generate_ical_filename(appointment)
    
    # Prepara i dati per i template (usa costanti da settings)
    context = {
        'appointment': appointment,
        'studio_name': settings.STUDIO_NAME,
        'studio_address': settings.STUDIO_ADDRESS,
        'studio_phone': settings.STUDIO_PHONE,
        'studio_email': settings.STUDIO_EMAIL,
        'studio_pec': settings.STUDIO_PEC,
        'studio_website': settings.STUDIO_WEBSITE,
        'studio_maps_url': settings.STUDIO_MAPS_URL,
    }
    
    results = {'client': False, 'studio': False, 'errors': []}
    
    # Email al cliente
    try:
        _send_client_email(appointment, context, ical_content, ical_filename)
        results['client'] = True
    except Exception as e:
        results['errors'].append(f"Cliente ({appointment.email}): {e}")
    
    # Email allo studio
    try:
        _send_studio_email(appointment, context, ical_content, ical_filename)
        results['studio'] = True
    except Exception as e:
        results['errors'].append(f"Studio ({settings.STUDIO_EMAIL}): {e}")
    
    if results['errors']:
        logger.warning(f"Errori invio email per appuntamento #{appointment.id}: {results['errors']}")
    else:
        logger.info(f"Email inviate con successo per appuntamento #{appointment.id}")
    
    return results


def _send_client_email(appointment, context, ical_content, ical_filename):
    """Invia email di conferma al cliente."""
    subject = f"Conferma prenotazione - Studio Legale D'Onofrio"
    
    # Formatta la data in italiano
    data_italiana = format_date_italian(appointment.date)
    
    # Corpo email testuale
    if appointment.consultation_type == 'video':
        text_content = f"""Gentile {appointment.first_name} {appointment.last_name},

La tua prenotazione è stata confermata!

DETTAGLI APPUNTAMENTO:
- Data: {data_italiana}
- Ora: {appointment.time.strftime('%H:%M')}
- Modalità: Videochiamata

LINK PER LA VIDEOCHIAMATA:
{appointment.jitsi_url}

Collegati qualche minuto prima dell'orario previsto.

Per qualsiasi informazione:
Mobile: {context['studio_phone']}
Email: {context['studio_email']}

Trovi in allegato il file calendario (.ics) da aggiungere al tuo calendario.
Riceverai un promemoria automatico 1 ora prima dell'appuntamento.

Cordiali saluti,

{context['studio_name']}
{context['studio_address']}
Email: {context['studio_email']}
PEC: {context['studio_pec']}
Mobile: {context['studio_phone']}
Web: {context['studio_website']}
"""
    else:
        text_content = f"""Gentile {appointment.first_name} {appointment.last_name},

La tua prenotazione è stata confermata!

DETTAGLI APPUNTAMENTO:
- Data: {data_italiana}
- Ora: {appointment.time.strftime('%H:%M')}
- Modalità: In presenza

DOVE TROVARCI:
Studio Legale D'Onofrio - {context['studio_name']}
{context['studio_address']}

Mappa: {context['studio_maps_url']}

Per qualsiasi informazione:
Mobile: {context['studio_phone']}
Email: {context['studio_email']}

Trovi in allegato il file calendario (.ics) da aggiungere al tuo calendario.
Riceverai un promemoria automatico 1 ora prima dell'appuntamento.

Cordiali saluti,

{context['studio_name']}
{context['studio_address']}
Email: {context['studio_email']}
PEC: {context['studio_pec']}
Mobile: {context['studio_phone']}
Web: {context['studio_website']}
"""
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[appointment.email],
    )
    
    # Allega il file iCal
    email.attach(ical_filename, ical_content, 'text/calendar')
    
    try:
        result = email.send()
        logger.info(f"Email cliente inviata a {appointment.email} (result={result})")
        return result
    except Exception as e:
        logger.error(f"ERRORE invio email cliente a {appointment.email}: {type(e).__name__}: {e}")
        raise


def _send_studio_email(appointment, context, ical_content, ical_filename):
    """Invia email di notifica allo studio."""
    subject = f"Nuova prenotazione: {appointment.first_name} {appointment.last_name} - {appointment.date.strftime('%d/%m/%Y')} ore {appointment.time.strftime('%H:%M')}"
    
    consultation_type = "Videochiamata" if appointment.consultation_type == 'video' else "In presenza"
    data_italiana = format_date_italian(appointment.date)
    
    text_content = f"""NUOVA PRENOTAZIONE RICEVUTA

CLIENTE:
- Nome: {appointment.first_name} {appointment.last_name}
- Email: {appointment.email}
- Telefono: {appointment.phone}

APPUNTAMENTO:
- Data: {data_italiana}
- Ora: {appointment.time.strftime('%H:%M')}
- Modalità: {consultation_type}
"""
    
    if appointment.consultation_type == 'video':
        text_content += f"""
LINK VIDEOCHIAMATA:
{appointment.jitsi_url}
"""
    
    if appointment.notes:
        text_content += f"""
NOTE DEL CLIENTE:
{appointment.notes}
"""
    
    text_content += """
---
Il file calendario (.ics) è allegato a questa email.
"""
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.STUDIO_EMAIL],  # Email dello studio
        reply_to=[appointment.email],  # Per rispondere direttamente al cliente
    )
    
    # Allega il file iCal
    email.attach(ical_filename, ical_content, 'text/calendar')
    
    try:
        result = email.send()
        logger.info(f"Email studio inviata a {settings.STUDIO_EMAIL} (result={result})")
        return result
    except Exception as e:
        logger.error(f"ERRORE invio email studio a {settings.STUDIO_EMAIL}: {type(e).__name__}: {e}")
        raise
