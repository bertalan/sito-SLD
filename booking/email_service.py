"""
Servizio email per invio conferme prenotazione con allegato iCal.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .ical import generate_ical, generate_ical_filename


def send_booking_confirmation(appointment):
    """
    Invia email di conferma al cliente e allo studio con allegato iCal.
    """
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
    
    # Email al cliente
    _send_client_email(appointment, context, ical_content, ical_filename)
    
    # Email allo studio
    _send_studio_email(appointment, context, ical_content, ical_filename)


def _send_client_email(appointment, context, ical_content, ical_filename):
    """Invia email di conferma al cliente."""
    subject = f"Conferma prenotazione - Studio Legale D'Onofrio"
    
    # Corpo email testuale
    if appointment.consultation_type == 'video':
        text_content = f"""Gentile {appointment.first_name} {appointment.last_name},

La tua prenotazione è stata confermata!

DETTAGLI APPUNTAMENTO:
- Data: {appointment.date.strftime('%A %d %B %Y')}
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
- Data: {appointment.date.strftime('%A %d %B %Y')}
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
        email.send()
    except Exception as e:
        print(f"Errore invio email cliente: {e}")


def _send_studio_email(appointment, context, ical_content, ical_filename):
    """Invia email di notifica allo studio."""
    subject = f"Nuova prenotazione: {appointment.first_name} {appointment.last_name} - {appointment.date.strftime('%d/%m/%Y')} ore {appointment.time.strftime('%H:%M')}"
    
    consultation_type = "Videochiamata" if appointment.consultation_type == 'video' else "In presenza"
    
    text_content = f"""NUOVA PRENOTAZIONE RICEVUTA

CLIENTE:
- Nome: {appointment.first_name} {appointment.last_name}
- Email: {appointment.email}
- Telefono: {appointment.phone}

APPUNTAMENTO:
- Data: {appointment.date.strftime('%A %d %B %Y')}
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
        email.send()
    except Exception as e:
        print(f"Errore invio email studio: {e}")
