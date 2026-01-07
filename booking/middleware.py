"""
Middleware per sincronizzazione Google Calendar in background.
Sincronizza eventi ogni 15 minuti su qualsiasi richiesta (anche spider).
"""
import threading
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Chiave cache per evitare sync troppo frequenti
SYNC_CACHE_KEY = 'google_calendar_sync_in_progress'
SYNC_CACHE_TTL = 900  # 15 minuti


def sync_google_calendar_in_background():
    """
    Avvia la sincronizzazione Google Calendar in un thread separato.
    Non blocca la risposta HTTP.
    """
    def _sync():
        try:
            from .google_calendar import sync_google_calendar_events
            sync_google_calendar_events()
            logger.debug("Google Calendar sync completato in background")
        except Exception as e:
            logger.error(f"Errore nel sync Google Calendar in background: {e}")
    
    # Lancia in thread daemon (non blocca lo shutdown)
    thread = threading.Thread(target=_sync, daemon=True)
    thread.start()


class GoogleCalendarSyncMiddleware:
    """
    Middleware che sincronizza Google Calendar in background su ogni richiesta.
    
    - Usa cache per evitare sync troppo frequenti (TTL 15 minuti)
    - Sync avviene in thread separato (non blocca la risposta)
    - Funziona anche con spider/bot
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Controlla se è il momento di sincronizzare
        sync_in_progress = cache.get(SYNC_CACHE_KEY)
        
        if not sync_in_progress:
            # Imposta cache per evitare sync simultanei
            cache.set(SYNC_CACHE_KEY, True, SYNC_CACHE_TTL)
            
            # Lancia sync in background
            sync_google_calendar_in_background()
        
        # Processa la richiesta normalmente (non blocca)
        response = self.get_response(request)
        
        return response
