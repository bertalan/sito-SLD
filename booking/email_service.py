"""
Servizio email per invio conferme prenotazione con allegato iCal.
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .ical import generate_ical, generate_ical_filename

logger = logging.getLogger(__name__)


def _get_studio_settings():
    """Recupera le impostazioni studio da SiteSettings o fallback su settings.py."""
    try:
        from sld_project.models import SiteSettings
        site_settings = SiteSettings.get_current()
        return {
            'studio_name': site_settings.lawyer_name or settings.STUDIO_NAME,
            'studio_address': site_settings.address or settings.STUDIO_ADDRESS,
            'studio_phone': site_settings.phone or settings.STUDIO_PHONE,
            'studio_mobile': site_settings.mobile_phone or '',
            'studio_email': site_settings.email or settings.STUDIO_EMAIL,
            'studio_pec': site_settings.email_pec or settings.STUDIO_PEC,
            'studio_website': site_settings.website or settings.STUDIO_WEBSITE,
            'studio_maps_url': site_settings.maps_url or settings.STUDIO_MAPS_URL,
        }
    except Exception:
        # Fallback su settings.py
        return {
            'studio_name': settings.STUDIO_NAME,
            'studio_address': settings.STUDIO_ADDRESS,
            'studio_phone': settings.STUDIO_PHONE,
            'studio_mobile': '',
            'studio_email': settings.STUDIO_EMAIL,
            'studio_pec': settings.STUDIO_PEC,
            'studio_website': settings.STUDIO_WEBSITE,
            'studio_maps_url': settings.STUDIO_MAPS_URL,
        }


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
    Invia email di avviso al cliente e allo studio con allegato iCal.
    Ritorna un dict con lo stato di invio per ogni destinatario.
    """
    logger.info(f"Invio email di avviso per appuntamento #{appointment.id} - {appointment.email}")
    
    # Genera il file iCal
    ical_content = generate_ical(appointment)
    ical_filename = generate_ical_filename(appointment)
    
    # Prepara i dati per i template (usa SiteSettings con fallback su settings.py)
    studio = _get_studio_settings()
    context = {
        'appointment': appointment,
        **studio,
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
    """Invia email di avviso al cliente."""
    subject = f"Avviso prenotazione - Studio Legale"
    
    # Formatta la data in italiano
    data_italiana = format_date_italian(appointment.date)
    
    # Orari e durata dinamici
    ora_inizio = appointment.time.strftime('%H:%M')
    ora_fine = appointment.end_time.strftime('%H:%M')
    durata = appointment.duration_minutes
    importo = appointment.total_price_display
    
    # Corpo email testuale
    if appointment.consultation_type == 'video':
        text_content = f"""Gentile {appointment.first_name} {appointment.last_name},

La tua prenotazione è stata ricevuta!

DETTAGLI APPUNTAMENTO:
- Data: {data_italiana}
- Orario: {ora_inizio} - {ora_fine} ({durata} minuti)
- Modalità: Videochiamata
- Importo: €{importo}

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

La tua prenotazione è stata ricevuta!

DETTAGLI APPUNTAMENTO:
- Data: {data_italiana}
- Orario: {ora_inizio} - {ora_fine} ({durata} minuti)
- Modalità: In presenza
- Importo: €{importo}

DOVE TROVARCI:
Studio Legale - {context['studio_name']}
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
    ora_inizio = appointment.time.strftime('%H:%M')
    ora_fine = appointment.end_time.strftime('%H:%M')
    
    subject = f"Nuova prenotazione: {appointment.first_name} {appointment.last_name} - {appointment.date.strftime('%d/%m/%Y')} ore {ora_inizio}-{ora_fine}"
    
    consultation_type = "Videochiamata" if appointment.consultation_type == 'video' else "In presenza"
    data_italiana = format_date_italian(appointment.date)
    durata = appointment.duration_minutes
    importo = appointment.total_price_display
    
    text_content = f"""NUOVA PRENOTAZIONE RICEVUTA

CLIENTE:
- Nome: {appointment.first_name} {appointment.last_name}
- Email: {appointment.email}
- Telefono: {appointment.phone}

APPUNTAMENTO:
- Data: {data_italiana}
- Orario: {ora_inizio} - {ora_fine} ({durata} minuti)
- Modalità: {consultation_type}
- Importo: €{importo}
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


def send_payment_link_email(appointment, payment_url):
    """
    Invia email al cliente con il link per completare il pagamento.
    
    Args:
        appointment: Istanza Appointment
        payment_url: URL completo per il pagamento
    
    Returns:
        bool: True se l'email è stata inviata
    """
    context = _get_studio_settings()
    data_italiana = format_date_italian(appointment.date)
    ora_inizio = appointment.time.strftime('%H:%M')
    ora_fine = appointment.end_time.strftime('%H:%M')
    importo = appointment.total_price_display
    
    metodo_display = "Carta di credito" if appointment.payment_method == 'stripe' else "PayPal"
    
    subject = f"Completa il pagamento - Appuntamento {data_italiana}"
    
    text_content = f"""Gentile {appointment.first_name},

Ti inviamo il link per completare il pagamento del tuo appuntamento.

RIEPILOGO APPUNTAMENTO:
- Data: {data_italiana}
- Orario: {ora_inizio} - {ora_fine}
- Importo: €{importo}
- Metodo di pagamento: {metodo_display}

Per completare il pagamento, clicca sul seguente link:
{payment_url}

Il link è valido per le prossime 24 ore.

Se hai bisogno di assistenza o desideri modificare il metodo di pagamento, 
contattaci rispondendo a questa email.

Cordiali saluti,

{context['studio_name']}
{context['studio_address']}
Email: {context['studio_email']}
PEC: {context['studio_pec']}
Tel: {context['studio_phone']}
"""
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[appointment.email],
        reply_to=[context['studio_email']],
    )
    
    try:
        result = email.send()
        logger.info(f"Email link pagamento inviata a {appointment.email} (result={result})")
        return bool(result)
    except Exception as e:
        logger.error(f"ERRORE invio email link pagamento a {appointment.email}: {type(e).__name__}: {e}")
        return False


def send_refund_notification(appointment, refund_id):
    """
    Invia email al cliente per confermare l'avvenuto rimborso.
    
    Args:
        appointment: Istanza Appointment
        refund_id: ID del rimborso effettuato
    
    Returns:
        bool: True se l'email è stata inviata
    """
    context = _get_studio_settings()
    data_italiana = format_date_italian(appointment.date)
    ora_inizio = appointment.time.strftime('%H:%M')
    importo = appointment.amount_paid
    
    metodo_display = "Carta di credito (Stripe)" if appointment.payment_method == 'stripe' else "PayPal"
    
    subject = f"Conferma rimborso - Appuntamento del {data_italiana}"
    
    text_content = f"""Gentile {appointment.first_name},

Ti confermiamo che il rimborso relativo al tuo appuntamento è stato effettuato con successo.

DETTAGLI RIMBORSO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Appuntamento:     {data_italiana} ore {ora_inizio}
💰 Importo rimborsato: €{importo:.2f}
💳 Metodo:           {metodo_display}
🔖 ID Rimborso:      {refund_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEMPISTICHE:
Il rimborso verrà accreditato sul tuo metodo di pagamento originale entro:
- Carte di credito/debito: 5-10 giorni lavorativi
- PayPal: 3-5 giorni lavorativi

Se dopo questo periodo non hai ricevuto il rimborso, ti preghiamo di:
1. Verificare l'estratto conto del metodo di pagamento utilizzato
2. Contattare la tua banca o PayPal con l'ID rimborso sopra indicato
3. Contattarci per ulteriore assistenza

Ci scusiamo per eventuali disagi e ti ringraziamo per la comprensione.

Cordiali saluti,

{context['studio_name']}
{context['studio_address']}
Email: {context['studio_email']}
PEC: {context['studio_pec']}
Tel: {context['studio_phone']}
"""
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0; background-color: #f3f4f6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <div style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            
            <!-- Header con icona rimborso -->
            <div style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 32px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 12px;">✅</div>
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">
                    Rimborso Confermato
                </h1>
            </div>
            
            <!-- Corpo email -->
            <div style="padding: 32px;">
                <p style="margin: 0 0 24px 0; color: #374151;">
                    Gentile <strong>{appointment.first_name}</strong>,
                </p>
                <p style="margin: 0 0 24px 0; color: #374151;">
                    Ti confermiamo che il rimborso relativo al tuo appuntamento è stato effettuato con successo.
                </p>
                
                <!-- Box dettagli rimborso -->
                <div style="background-color: #ecfdf5; border-radius: 8px; padding: 24px; margin: 24px 0;">
                    <h3 style="margin: 0 0 16px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #059669;">
                        Dettagli Rimborso
                    </h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">📅 Appuntamento:</td>
                            <td style="padding: 8px 0; text-align: right; font-weight: 600;">{data_italiana} ore {ora_inizio}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">💰 Importo rimborsato:</td>
                            <td style="padding: 8px 0; text-align: right; font-weight: 600; color: #059669; font-size: 18px;">€{importo:.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">💳 Metodo:</td>
                            <td style="padding: 8px 0; text-align: right; font-weight: 600;">{metodo_display}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">🔖 ID Rimborso:</td>
                            <td style="padding: 8px 0; text-align: right; font-family: monospace; font-size: 12px; color: #6b7280;">{refund_id}</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Info tempistiche -->
                <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                    <h4 style="margin: 0 0 8px 0; color: #92400e;">⏱️ Tempistiche accredito</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #78350f;">
                        <li>Carte di credito/debito: 5-10 giorni lavorativi</li>
                        <li>PayPal: 3-5 giorni lavorativi</li>
                    </ul>
                </div>
                
                <p style="margin: 24px 0 0 0; color: #6b7280; font-size: 14px;">
                    Ci scusiamo per eventuali disagi e ti ringraziamo per la comprensione.
                </p>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f9fafb; padding: 24px 32px; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0; font-size: 14px; color: #6b7280;">
                    <strong>{context['studio_name']}</strong><br>
                    {context['studio_address']}<br>
                    📧 {context['studio_email']}<br>
                    📞 {context['studio_phone']}
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[appointment.email],
        reply_to=[context['studio_email']],
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        result = email.send()
        logger.info(f"Email rimborso inviata a {appointment.email} per appuntamento {appointment.pk} (result={result})")
        return bool(result)
    except Exception as e:
        logger.error(f"ERRORE invio email rimborso a {appointment.email}: {type(e).__name__}: {e}")
        return False
