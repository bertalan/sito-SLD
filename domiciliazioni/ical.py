"""
Generatore file iCal per udienze domiciliazioni.
"""
from datetime import datetime, timedelta
from django.conf import settings
import hashlib

# Mapping tribunali per indirizzo
TRIBUNALI_INDIRIZZI = {
    'lecce': 'Tribunale di Lecce, Viale Michele De Pietro, 73100 Lecce LE',
    'brindisi': 'Tribunale di Brindisi, Via Nazario Sauro, 72100 Brindisi BR',
    'taranto': 'Tribunale di Taranto, Viale Virgilio, 74121 Taranto TA',
    'bari': 'Tribunale di Bari, Piazza Enrico De Nicola, 70122 Bari BA',
}


def generate_domiciliazione_ical(submission):
    """
    Genera un file iCal (.ics) per l'udienza di domiciliazione.
    Include reminder 1 giorno prima e 2 ore prima.
    """
    # Se non c'è ora, usa le 9:00 come default
    ora = submission.ora_udienza or datetime.strptime('09:00', '%H:%M').time()
    
    # Combina data e ora
    start_dt = datetime.combine(submission.data_udienza, ora)
    # Durata presunta udienza: 1 ora
    end_dt = start_dt + timedelta(hours=1)
    
    # Formatta per iCal (formato: YYYYMMDDTHHMMSS)
    def format_datetime(dt):
        return dt.strftime('%Y%m%dT%H%M%S')
    
    # UID univoco per l'evento
    uid = hashlib.sha256(
        f"dom-{submission.id}-{submission.data_udienza}-{submission.numero_rg}".encode()
    ).hexdigest()[:32]
    
    # Tribunale display
    tribunale_display = {
        'lecce': 'Tribunale di Lecce',
        'brindisi': 'Tribunale di Brindisi',
        'taranto': 'Tribunale di Taranto',
        'bari': 'Tribunale di Bari',
    }.get(submission.tribunale, submission.tribunale)
    
    # Location
    location = TRIBUNALI_INDIRIZZI.get(submission.tribunale, tribunale_display)
    if submission.sezione:
        location += f" - {submission.sezione}"
    
    # Tipo udienza display
    tipo_display = {
        'civile': 'Udienza Civile',
        'penale': 'Udienza Penale',
        'lavoro': 'Udienza Lavoro',
        'famiglia': 'Udienza Famiglia',
        'esecuzioni': 'Esecuzioni',
        'fallimentare': 'Fallimentare',
        'volontaria': 'Volontaria Giurisdizione',
        'altro': 'Altro',
    }.get(submission.tipo_udienza, submission.tipo_udienza)
    
    # Descrizione dettagliata
    description = f"""DOMICILIAZIONE - {tribunale_display}

R.G.: {submission.numero_rg}
Tipo: {tipo_display}
Giudice: {submission.giudice or 'Non specificato'}
Parti: {submission.parti_causa or 'Non specificate'}

AVVOCATO RICHIEDENTE:
{submission.nome_avvocato}
Email: {submission.email}
Tel: {submission.telefono or 'Non indicato'}
Ordine: {submission.ordine_appartenenza or 'Non indicato'}

ATTIVITÀ DA SVOLGERE:
{submission.attivita_richieste or 'Mera comparizione'}

NOTE:
{submission.note or 'Nessuna nota'}

---
Studio Legale D'Onofrio
{getattr(settings, 'STUDIO_PHONE', '+39 320 7044664')}
{getattr(settings, 'STUDIO_EMAIL', 'info@studiolegaledonofrio.it')}"""
    
    # Escape caratteri speciali per iCal
    def escape_ical(text):
        return text.replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
    
    # Timestamp creazione
    dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    
    # Summary
    summary = f"Udienza {submission.numero_rg} - {tribunale_display}"
    
    ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Studio Legale D'Onofrio//Domiciliazioni//IT
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}@studiolegaledonofrio.it
DTSTAMP:{dtstamp}
DTSTART:{format_datetime(start_dt)}
DTEND:{format_datetime(end_dt)}
SUMMARY:{escape_ical(summary)}
LOCATION:{escape_ical(location)}
DESCRIPTION:{escape_ical(description)}
ORGANIZER;CN=Studio Legale D'Onofrio:mailto:{getattr(settings, 'STUDIO_EMAIL', 'info@studiolegaledonofrio.it')}
ATTENDEE;CN={escape_ical(submission.nome_avvocato)};RSVP=TRUE:mailto:{submission.email}
STATUS:CONFIRMED
TRANSP:OPAQUE
PRIORITY:1
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:Promemoria: Udienza domani - R.G. {submission.numero_rg}
END:VALARM
BEGIN:VALARM
TRIGGER:-PT2H
ACTION:DISPLAY
DESCRIPTION:Promemoria: Udienza tra 2 ore - R.G. {submission.numero_rg}
END:VALARM
BEGIN:VALARM
TRIGGER:-PT2H
ACTION:EMAIL
SUMMARY:Promemoria: Udienza tra 2 ore - R.G. {submission.numero_rg}
DESCRIPTION:L'udienza presso {tribunale_display} inizierà tra 2 ore.
ATTENDEE:mailto:{submission.email}
END:VALARM
END:VEVENT
END:VCALENDAR"""
    
    return ical_content.strip()


def generate_domiciliazione_ical_filename(submission):
    """Genera il nome del file iCal per la domiciliazione."""
    date_str = submission.data_udienza.strftime('%Y%m%d')
    rg_clean = submission.numero_rg.replace('/', '-').replace(' ', '')
    return f"udienza-{submission.tribunale}-{rg_clean}-{date_str}.ics"
