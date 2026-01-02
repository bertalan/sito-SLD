"""
Generatore file iCal per udienze domiciliazioni.
"""
from datetime import datetime, timedelta
from django.conf import settings
import hashlib

# Mapping tribunali per indirizzo
TRIBUNALI_INDIRIZZI = {
    'roma': 'Tribunale di Roma, Viale Giulio Cesare 52, 00192 Roma RM',
    'corte_appello': "Corte d'Appello di Roma, Piazza Cavour, 00193 Roma RM",
    'gdp': 'Giudice di Pace di Roma, Viale Giulio Cesare 78, 00192 Roma RM',
    'tar': 'TAR Lazio, Via Flaminia 189, 00196 Roma RM',
    'unep': 'Ufficio UNEP di Roma, Viale Giulio Cesare 52, 00192 Roma RM',
}


def _get_studio_settings():
    """Recupera le impostazioni studio da SiteSettings o fallback su settings.py."""
    try:
        from sld_project.models import SiteSettings
        site_settings = SiteSettings.get_current()
        return {
            'name': site_settings.lawyer_name or getattr(settings, 'STUDIO_NAME', 'Avv. Mario Rossi'),
            'studio_name': site_settings.studio_name or "Studio Legale",
            'phone': site_settings.phone or getattr(settings, 'STUDIO_PHONE', '+39 06 12345678'),
            'mobile_phone': site_settings.mobile_phone or '',
            'email': site_settings.email or getattr(settings, 'STUDIO_EMAIL', 'info@example.com'),
            'website': site_settings.website or getattr(settings, 'STUDIO_WEBSITE', 'www.example.com'),
        }
    except Exception:
        return {
            'name': getattr(settings, 'STUDIO_NAME', 'Avv. Mario Rossi'),
            'studio_name': "Studio Legale",
            'phone': getattr(settings, 'STUDIO_PHONE', '+39 06 12345678'),
            'mobile_phone': '',
            'email': getattr(settings, 'STUDIO_EMAIL', 'info@example.com'),
            'website': getattr(settings, 'STUDIO_WEBSITE', 'www.example.com'),
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
    
    # Recupera impostazioni studio
    studio = _get_studio_settings()
    
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
{studio['studio_name']}
{studio['phone']}
{studio['email']}"""
    
    # Escape caratteri speciali per iCal
    def escape_ical(text):
        return text.replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
    
    # Timestamp creazione
    dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    
    # Summary
    summary = f"Udienza {submission.numero_rg} - {tribunale_display}"
    
    ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//{studio['studio_name']}//Domiciliazioni//IT
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}@{studio['website'].replace('www.', '')}
DTSTAMP:{dtstamp}
DTSTART:{format_datetime(start_dt)}
DTEND:{format_datetime(end_dt)}
SUMMARY:{escape_ical(summary)}
LOCATION:{escape_ical(location)}
DESCRIPTION:{escape_ical(description)}
ORGANIZER;CN={studio['studio_name']}:mailto:{studio['email']}
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
