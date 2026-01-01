"""
Servizio per sincronizzare eventi da Google Calendar.
Cerca eventi con prefisso "App " e li salva localmente.
"""
import requests
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def fetch_calendar_events():
    """
    Scarica e parsa il feed iCal del calendario Google.
    Restituisce lista di eventi con prefisso "App " (case insensitive).
    """
    try:
        from icalendar import Calendar
        
        ical_url = getattr(settings, 'GOOGLE_CALENDAR_ICAL_URL', '')
        if not ical_url:
            logger.warning("GOOGLE_CALENDAR_ICAL_URL non configurato")
            return []
        
        response = requests.get(ical_url, timeout=30)
        response.raise_for_status()
        
        cal = Calendar.from_ical(response.content)
        events = []
        now = timezone.now()
        
        for component in cal.walk():
            if component.name != 'VEVENT':
                continue
            
            summary = str(component.get('summary', ''))
            
            # Filtra solo eventi con prefisso "App " (case insensitive)
            if not summary.lower().startswith('app '):
                continue
            
            dtstart = component.get('dtstart')
            dtend = component.get('dtend')
            uid = str(component.get('uid', ''))
            
            if not dtstart:
                continue
            
            # Converti date in datetime
            start_dt = dtstart.dt
            if hasattr(start_dt, 'tzinfo') and start_dt.tzinfo is None:
                start_dt = timezone.make_aware(start_dt)
            elif not hasattr(start_dt, 'hour'):
                # È una data, non un datetime (evento tutto il giorno)
                start_dt = timezone.make_aware(datetime.combine(start_dt, datetime.min.time()))
            
            if dtend:
                end_dt = dtend.dt
                if hasattr(end_dt, 'tzinfo') and end_dt.tzinfo is None:
                    end_dt = timezone.make_aware(end_dt)
                elif not hasattr(end_dt, 'hour'):
                    end_dt = timezone.make_aware(datetime.combine(end_dt, datetime.min.time()))
            else:
                # Default: 30 minuti
                end_dt = start_dt + timedelta(minutes=30)
            
            events.append({
                'uid': uid,
                'summary': summary,
                'start': start_dt,
                'end': end_dt,
            })
        
        logger.info(f"Trovati {len(events)} eventi 'App' nel calendario Google")
        return events
        
    except Exception as e:
        logger.error(f"Errore nel fetch del calendario Google: {e}")
        return []


def sync_google_calendar_events():
    """
    Sincronizza gli eventi da Google Calendar al database locale.
    Usa cache per evitare chiamate troppo frequenti.
    """
    from .models import GoogleCalendarEvent
    
    cache_ttl = getattr(settings, 'GOOGLE_CALENDAR_CACHE_TTL', 600)
    
    # Check cache
    cache_key = 'google_calendar_last_sync'
    last_sync = cache.get(cache_key)
    
    if last_sync:
        logger.debug("Calendario Google già sincronizzato di recente, uso cache")
        return False
    
    events = fetch_calendar_events()
    
    if not events:
        # Se non ci sono eventi o errore, non aggiornare
        cache.set(cache_key, timezone.now(), cache_ttl)
        return False
    
    # Filtra solo eventi futuri (da oggi in poi)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    future_events = [e for e in events if e['end'] >= today]
    
    # Aggiorna database
    existing_uids = set(GoogleCalendarEvent.objects.values_list('google_uid', flat=True))
    incoming_uids = set(e['uid'] for e in future_events)
    
    # Elimina eventi rimossi dal calendario
    to_delete = existing_uids - incoming_uids
    if to_delete:
        GoogleCalendarEvent.objects.filter(google_uid__in=to_delete).delete()
        logger.info(f"Eliminati {len(to_delete)} eventi non più nel calendario")
    
    # Aggiorna o crea eventi
    for event in future_events:
        GoogleCalendarEvent.objects.update_or_create(
            google_uid=event['uid'],
            defaults={
                'summary': event['summary'],
                'start_datetime': event['start'],
                'end_datetime': event['end'],
                'synced_at': timezone.now(),
            }
        )
    
    # Imposta cache
    cache.set(cache_key, timezone.now(), cache_ttl)
    logger.info(f"Sincronizzati {len(future_events)} eventi 'App' da Google Calendar")
    
    return True


def get_blocked_slots_from_google(target_date):
    """
    Restituisce gli slot da 30 minuti bloccati da eventi Google Calendar per una data.
    
    Args:
        target_date: date object
        
    Returns:
        Set di time objects (inizio slot bloccati)
    """
    from .models import GoogleCalendarEvent
    
    # Sincronizza se necessario
    sync_google_calendar_events()
    
    # Trova eventi per la data richiesta
    events = GoogleCalendarEvent.objects.filter(
        start_datetime__date__lte=target_date,
        end_datetime__date__gte=target_date,
    )
    
    blocked_slots = set()
    
    for event in events:
        # Converti in timezone locale
        start = timezone.localtime(event.start_datetime)
        end = timezone.localtime(event.end_datetime)
        
        # Trova tutti gli slot da 30 minuti coperti dall'evento
        current = start.replace(minute=(start.minute // 30) * 30, second=0, microsecond=0)
        
        while current < end:
            if current.date() == target_date:
                blocked_slots.add(current.time())
            current += timedelta(minutes=30)
    
    return blocked_slots
