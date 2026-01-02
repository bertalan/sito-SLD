from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from datetime import datetime

from .models import DomiciliazioniSubmission, DomiciliazioniDocument, DomiciliazioniPage
from .ical import generate_domiciliazione_ical, generate_domiciliazione_ical_filename


def _get_studio_settings():
    """Recupera le impostazioni studio da SiteSettings o fallback su settings.py."""
    try:
        from sld_project.models import SiteSettings
        site_settings = SiteSettings.get_current()
        return {
            'name': site_settings.lawyer_name or getattr(settings, 'STUDIO_NAME', 'Avv. Mario Rossi'),
            'studio_name': site_settings.studio_name or "Studio Legale",
            'address': site_settings.address or getattr(settings, 'STUDIO_ADDRESS', 'Via Roma, 1 - 00100 Roma'),
            'phone': site_settings.phone or getattr(settings, 'STUDIO_PHONE', '+39 06 12345678'),
            'mobile_phone': site_settings.mobile_phone or '',
            'email': site_settings.email or getattr(settings, 'STUDIO_EMAIL', 'info@example.com'),
            'email_pec': site_settings.email_pec or getattr(settings, 'STUDIO_PEC', 'avvocato@pec.it'),
            'website': site_settings.website or getattr(settings, 'STUDIO_WEBSITE', 'www.example.com'),
        }
    except Exception:
        return {
            'name': getattr(settings, 'STUDIO_NAME', 'Avv. Mario Rossi'),
            'studio_name': "Studio Legale",
            'address': getattr(settings, 'STUDIO_ADDRESS', 'Via Roma, 1 - 00100 Roma'),
            'phone': getattr(settings, 'STUDIO_PHONE', '+39 06 12345678'),
            'mobile_phone': '',
            'email': getattr(settings, 'STUDIO_EMAIL', 'info@example.com'),
            'email_pec': getattr(settings, 'STUDIO_PEC', 'avvocato@pec.it'),
            'website': getattr(settings, 'STUDIO_WEBSITE', 'www.example.com'),
        }


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
    from .models import get_tribunale_choices, get_tipo_udienza_choices
    
    # Recupera impostazioni studio
    studio = _get_studio_settings()
    
    tribunale_display = dict(get_tribunale_choices()).get(
        submission.tribunale, submission.tribunale
    )
    tipo_display = dict(get_tipo_udienza_choices()).get(
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

ATTIVITÀ RICHIESTE:
- Tribunale/ufficio: {tribunale_display}
- Servizio: {tipo_display}
- Sezione: {submission.sezione or 'Non indicata'}
- Giudice: {submission.giudice or 'Non indicato'}

CAUSA:
- Numero R.G.: {submission.numero_rg}
- Parti: {submission.parti_causa or 'Non indicate'}
- Data udienza: {data_italiana}
- Ora udienza: {ora_str}

ATTIVITÀ RICHIESTE:
{submission.attivita_richieste or 'Nessuna attità richiesta'}

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
            from_email=studio['email'],
            to=[studio['email']],
            reply_to=[submission.email],
        )
        # Allega il file iCal
        email.attach(ical_filename, ical_content, 'text/calendar')
        # Allega i documenti caricati dall'utente
        for doc in submission.documents.all():
            try:
                doc.file.open('rb')
                email.attach(doc.original_filename, doc.file.read(), None)
                doc.file.close()
            except Exception as doc_err:
                print(f"Errore allegando documento {doc.original_filename}: {doc_err}")
        email.send()
    except Exception as e:
        print(f"Errore invio email domiciliazione: {e}")
    
    # Email di avviso all'avvocato
    confirm_subject = f"Avviso richiesta domiciliazione - R.G. {submission.numero_rg}"
    confirm_body = f"""Gentile Collega {submission.nome_avvocato},

La tua richiesta di domiciliazione è stata ricevuta correttamente.

RIEPILOGO:
- Tribunale/Attività: {tribunale_display}
- Servizio: {tipo_display}
- R.G.: {submission.numero_rg}
- Data udienza: {data_italiana}
- Ora: {ora_str}

Ti confermeremo la presa in carico al più presto.

In allegato si trova il file calendario (.ics) da aggiungere al proprio calendario.
Sarà inviato un promemoria automatico il giorno prima e 2 ore prima dell'udienza.

Cordiali saluti,
-- 
{studio['name']}
{studio['address']}
Email: {studio['email']}
PEC: {studio['email_pec']}
Mobile: {studio['phone']}
Web: {studio['website']}
"""
    
    try:
        confirm_email = EmailMultiAlternatives(
            subject=confirm_subject,
            body=confirm_body,
            from_email=studio['email'],
            to=[submission.email],
        )
        # Allega il file iCal
        confirm_email.attach(ical_filename, ical_content, 'text/calendar')
        confirm_email.send()
    except Exception as e:
        print(f"Errore invio email avviso: {e}")
