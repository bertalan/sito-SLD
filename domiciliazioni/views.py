from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from datetime import datetime

from .models import DomiciliazioniSubmission, DomiciliazioniDocument, DomiciliazioniPage
from .ical import generate_domiciliazione_ical, generate_domiciliazione_ical_filename

# Traduzioni italiane per giorni e mesi
GIORNI_IT = {
    'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
    'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica',
}
MESI_IT = {
    'January': 'Gennaio', 'February': 'Febbraio', 'March': 'Marzo', 'April': 'Aprile',
    'May': 'Maggio', 'June': 'Giugno', 'July': 'Luglio', 'August': 'Agosto',
    'September': 'Settembre', 'October': 'Ottobre', 'November': 'Novembre', 'December': 'Dicembre',
}

def format_date_italian(date):
    """Formatta una data in italiano (es: Venerdì 23 Gennaio 2026)."""
    day_it = GIORNI_IT.get(date.strftime('%A'), date.strftime('%A'))
    month_it = MESI_IT.get(date.strftime('%B'), date.strftime('%B'))
    return f"{day_it} {date.day} {month_it} {date.year}"


def process_domiciliazione_form(request, page):
    """Processa il form di domiciliazione."""
    if request.method != 'POST':
        return None
    
    try:
        # Estrai dati dal form
        data = request.POST
        
        # Parsing ora (può essere vuota)
        ora_udienza = None
        if data.get('ora_udienza'):
            try:
                ora_udienza = datetime.strptime(data['ora_udienza'], '%H:%M').time()
            except ValueError:
                pass
        
        # Crea submission
        submission = DomiciliazioniSubmission.objects.create(
            page=page,
            nome_avvocato=data['nome_avvocato'],
            email=data['email'],
            telefono=data.get('telefono', ''),
            ordine_appartenenza=data.get('ordine_appartenenza', ''),
            tribunale=data['tribunale'],
            sezione=data.get('sezione', ''),
            giudice=data.get('giudice', ''),
            tipo_udienza=data['tipo_udienza'],
            numero_rg=data['numero_rg'],
            parti_causa=data.get('parti_causa', ''),
            data_udienza=datetime.strptime(data['data_udienza'], '%Y-%m-%d').date(),
            ora_udienza=ora_udienza,
            attivita_richieste=data.get('attivita_richieste', ''),
            note=data.get('note', ''),
        )
        
        # Salva documenti allegati
        files = request.FILES.getlist('documents')
        for f in files:
            DomiciliazioniDocument.objects.create(
                submission=submission,
                file=f,
                original_filename=f.name
            )
        
        # Invia email di notifica
        send_domiciliazione_notification(submission)
        
        return submission
        
    except Exception as e:
        print(f"Errore processing domiciliazione: {e}")
        return None


def send_domiciliazione_notification(submission):
    """Invia email di notifica per nuova richiesta domiciliazione con allegato iCal."""
    
    tribunale_display = dict(submission.TRIBUNALE_CHOICES if hasattr(submission, 'TRIBUNALE_CHOICES') else []).get(
        submission.tribunale, submission.tribunale
    )
    tipo_display = dict(submission.TIPO_UDIENZA_CHOICES if hasattr(submission, 'TIPO_UDIENZA_CHOICES') else []).get(
        submission.tipo_udienza, submission.tipo_udienza
    )
    
    ora_str = submission.ora_udienza.strftime('%H:%M') if submission.ora_udienza else 'Da definire'
    data_italiana = format_date_italian(submission.data_udienza)
    
    # Genera file iCal
    ical_content = generate_domiciliazione_ical(submission)
    ical_filename = generate_domiciliazione_ical_filename(submission)
    
    # Email allo studio
    subject = f"Nuova richiesta domiciliazione - R.G. {submission.numero_rg} - {tribunale_display}"
    
    body = f"""NUOVA RICHIESTA DOMICILIAZIONE

AVVOCATO RICHIEDENTE:
- Nome: {submission.nome_avvocato}
- Email: {submission.email}
- Telefono: {submission.telefono or 'Non indicato'}
- Ordine: {submission.ordine_appartenenza or 'Non indicato'}

TRIBUNALE:
- Tribunale: {tribunale_display}
- Sezione: {submission.sezione or 'Non indicata'}
- Giudice: {submission.giudice or 'Non indicato'}
- Tipo udienza: {tipo_display}

CAUSA:
- Numero R.G.: {submission.numero_rg}
- Parti: {submission.parti_causa or 'Non indicate'}
- Data udienza: {data_italiana}
- Ora udienza: {ora_str}

ATTIVITÀ RICHIESTE:
{submission.attivita_richieste or 'Mera comparizione'}

NOTE:
{submission.note or 'Nessuna nota'}

---
Documenti allegati: {submission.documents.count()}
File calendario (.ics) allegato.
"""
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@studiolegaledonofrio.it'),
            to=[getattr(settings, 'STUDIO_EMAIL', 'info@studiolegaledonofrio.it')],
            reply_to=[submission.email],
        )
        # Allega il file iCal
        email.attach(ical_filename, ical_content, 'text/calendar')
        email.send()
    except Exception as e:
        print(f"Errore invio email domiciliazione: {e}")
    
    # Email di conferma all'avvocato
    confirm_subject = f"Conferma richiesta domiciliazione - R.G. {submission.numero_rg}"
    confirm_body = f"""Gentile {submission.nome_avvocato},

La Sua richiesta di domiciliazione è stata ricevuta correttamente.

RIEPILOGO:
- Tribunale: {tribunale_display}
- R.G.: {submission.numero_rg}
- Data udienza: {data_italiana}
- Ora: {ora_str}

Le confermeremo la presa in carico al più presto.

Trovi in allegato il file calendario (.ics) da aggiungere al Suo calendario.
Riceverà un promemoria automatico il giorno prima e 2 ore prima dell'udienza.

Cordiali saluti,
RD
-- 
{getattr(settings, 'STUDIO_NAME', "Avv. Rossella D'Onofrio")}
{getattr(settings, 'STUDIO_ADDRESS', 'Piazza G. Mazzini, 72 - 73100 Lecce')}
Email: {getattr(settings, 'STUDIO_EMAIL', 'info@studiolegaledonofrio.it')}
PEC: {getattr(settings, 'STUDIO_PEC', 'rossella.donofrio@pec.it')}
Mobile: {getattr(settings, 'STUDIO_PHONE', '+39 320 7044664')}
Web: {getattr(settings, 'STUDIO_WEBSITE', 'www.studiolegaledonofrio.it')}
"""
    
    try:
        confirm_email = EmailMultiAlternatives(
            subject=confirm_subject,
            body=confirm_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@studiolegaledonofrio.it'),
            to=[submission.email],
        )
        # Allega il file iCal
        confirm_email.attach(ical_filename, ical_content, 'text/calendar')
        confirm_email.send()
    except Exception as e:
        print(f"Errore invio email conferma: {e}")
