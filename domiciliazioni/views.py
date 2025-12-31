from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from datetime import datetime

from .models import DomiciliazioniSubmission, DomiciliazioniDocument, DomiciliazioniPage


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
    """Invia email di notifica per nuova richiesta domiciliazione."""
    
    tribunale_display = dict(submission.TRIBUNALE_CHOICES if hasattr(submission, 'TRIBUNALE_CHOICES') else []).get(
        submission.tribunale, submission.tribunale
    )
    tipo_display = dict(submission.TIPO_UDIENZA_CHOICES if hasattr(submission, 'TIPO_UDIENZA_CHOICES') else []).get(
        submission.tipo_udienza, submission.tipo_udienza
    )
    
    ora_str = submission.ora_udienza.strftime('%H:%M') if submission.ora_udienza else 'Da definire'
    
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
- Data udienza: {submission.data_udienza.strftime('%d/%m/%Y')}
- Ora udienza: {ora_str}

ATTIVITÀ RICHIESTE:
{submission.attivita_richieste or 'Mera comparizione'}

NOTE:
{submission.note or 'Nessuna nota'}

---
Documenti allegati: {submission.documents.count()}
"""
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@studiolegaledonofrio.it'),
            to=[getattr(settings, 'STUDIO_EMAIL', 'info@studiolegaledonofrio.it')],
            reply_to=[submission.email],
        )
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
- Data udienza: {submission.data_udienza.strftime('%d/%m/%Y')}
- Ora: {ora_str}

Le confermeremo la presa in carico al più presto.

Cordiali saluti,
RD
-- 
{getattr(settings, 'STUDIO_NAME', 'Avv. Rossella D\\'Onofrio')}
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
        confirm_email.send()
    except Exception as e:
        print(f"Errore invio email conferma: {e}")
