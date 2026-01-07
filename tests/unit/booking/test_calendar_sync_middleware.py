"""
Test TDD per GoogleCalendarSyncMiddleware.
Verifica che il sync venga lanciato in background su ogni richiesta.
"""
import pytest
import time
from unittest.mock import patch, MagicMock, call
from django.test import RequestFactory, TestCase
from django.core.cache import cache
from django.http import HttpResponse


class TestGoogleCalendarSyncMiddleware(TestCase):
    """Test per il middleware di sincronizzazione Google Calendar."""
    
    def setUp(self):
        """Setup per ogni test."""
        self.factory = RequestFactory()
        cache.clear()
        
    def tearDown(self):
        """Cleanup dopo ogni test."""
        cache.clear()
    
    def test_middleware_exists(self):
        """Verifica che il middleware sia definito."""
        from booking.middleware import GoogleCalendarSyncMiddleware
        assert GoogleCalendarSyncMiddleware is not None
    
    def test_middleware_does_not_block_response(self):
        """Verifica che il middleware non blocchi la risposta HTTP."""
        from booking.middleware import GoogleCalendarSyncMiddleware
        
        # Mock get_response che ritorna dopo 0.1s
        def slow_get_response(request):
            time.sleep(0.1)
            return HttpResponse("OK")
        
        middleware = GoogleCalendarSyncMiddleware(slow_get_response)
        request = self.factory.get('/')
        
        start = time.time()
        response = middleware(request)
        elapsed = time.time() - start
        
        # La risposta deve arrivare velocemente (< 0.2s)
        # Anche se il sync in background è lento, non deve bloccare
        assert elapsed < 0.3, f"Middleware ha bloccato per {elapsed}s"
        assert response.status_code == 200
    
    @patch('booking.middleware.sync_google_calendar_in_background')
    def test_middleware_triggers_sync_on_first_request(self, mock_sync):
        """Verifica che il middleware lanci il sync alla prima richiesta."""
        from booking.middleware import GoogleCalendarSyncMiddleware
        
        def get_response(request):
            return HttpResponse("OK")
        
        middleware = GoogleCalendarSyncMiddleware(get_response)
        request = self.factory.get('/')
        
        response = middleware(request)
        
        assert response.status_code == 200
        # Sync deve essere chiamato
        assert mock_sync.called
    
    @patch('booking.middleware.sync_google_calendar_in_background')
    def test_middleware_respects_cache_ttl(self, mock_sync):
        """Verifica che il middleware rispetti il TTL della cache (15 minuti)."""
        from booking.middleware import GoogleCalendarSyncMiddleware
        
        def get_response(request):
            return HttpResponse("OK")
        
        middleware = GoogleCalendarSyncMiddleware(get_response)
        
        # Prima richiesta: deve chiamare sync
        request1 = self.factory.get('/')
        middleware(request1)
        assert mock_sync.call_count == 1
        
        # Seconda richiesta entro TTL: NON deve chiamare sync
        request2 = self.factory.get('/about/')
        middleware(request2)
        assert mock_sync.call_count == 1  # Ancora 1, non 2
    
    @patch('booking.middleware.sync_google_calendar_in_background')
    def test_middleware_syncs_after_cache_expiry(self, mock_sync):
        """Verifica che il middleware ri-sincronizzi dopo la scadenza della cache."""
        from booking.middleware import GoogleCalendarSyncMiddleware
        
        def get_response(request):
            return HttpResponse("OK")
        
        middleware = GoogleCalendarSyncMiddleware(get_response)
        
        # Prima richiesta
        request1 = self.factory.get('/')
        middleware(request1)
        assert mock_sync.call_count == 1
        
        # Simula scadenza cache
        cache.delete('google_calendar_sync_in_progress')
        
        # Seconda richiesta dopo scadenza: deve chiamare sync
        request2 = self.factory.get('/')
        middleware(request2)
        assert mock_sync.call_count == 2
    
    @patch('booking.middleware.threading.Thread')
    @patch('booking.google_calendar.sync_google_calendar_events')
    def test_sync_runs_in_separate_thread(self, mock_sync_fn, mock_thread):
        """Verifica che il sync venga eseguito in un thread separato."""
        from booking.middleware import sync_google_calendar_in_background
        
        sync_google_calendar_in_background()
        
        # Deve creare un thread
        assert mock_thread.called
        # Deve passare la funzione sync come target
        call_kwargs = mock_thread.call_args[1]
        assert 'target' in call_kwargs
        assert call_kwargs['daemon'] is True
    
    @patch('booking.middleware.sync_google_calendar_in_background')
    def test_middleware_handles_admin_requests(self, mock_sync):
        """Verifica che il middleware non interferisca con richieste admin."""
        from booking.middleware import GoogleCalendarSyncMiddleware
        
        def get_response(request):
            return HttpResponse("OK")
        
        middleware = GoogleCalendarSyncMiddleware(get_response)
        
        # Richiesta admin
        request = self.factory.get('/admin/booking/appointment/')
        response = middleware(request)
        
        assert response.status_code == 200
        # Anche per admin deve sincronizzare (spider possono visitare qualsiasi pagina)
        assert mock_sync.called
    
    @patch('booking.middleware.sync_google_calendar_in_background')
    def test_middleware_handles_static_requests(self, mock_sync):
        """Verifica che il middleware gestisca richieste a risorse statiche."""
        from booking.middleware import GoogleCalendarSyncMiddleware
        
        def get_response(request):
            return HttpResponse("OK")
        
        middleware = GoogleCalendarSyncMiddleware(get_response)
        
        # Richiesta a file statico
        request = self.factory.get('/static/css/main.css')
        response = middleware(request)
        
        assert response.status_code == 200
        # Per file statici potremmo decidere di NON sincronizzare
        # ma per semplicità sincronizziamo sempre
    
    @patch('booking.google_calendar.sync_google_calendar_events')
    def test_sync_function_catches_exceptions(self, mock_sync_events):
        """Verifica che errori nel sync non crashino l'applicazione."""
        from booking.middleware import sync_google_calendar_in_background
        
        # Simula errore nel sync
        mock_sync_events.side_effect = Exception("Google Calendar API error")
        
        # Non deve sollevare eccezione
        try:
            sync_google_calendar_in_background()
            # Attendi che il thread finisca
            time.sleep(0.2)
        except Exception as e:
            pytest.fail(f"sync_google_calendar_in_background ha sollevato eccezione: {e}")
    
    @patch('booking.middleware.sync_google_calendar_in_background')
    def test_middleware_works_with_spider_user_agents(self, mock_sync):
        """Verifica che il middleware funzioni anche con spider/bot."""
        from booking.middleware import GoogleCalendarSyncMiddleware
        
        def get_response(request):
            return HttpResponse("OK")
        
        middleware = GoogleCalendarSyncMiddleware(get_response)
        
        # Simula richiesta da Googlebot
        request = self.factory.get('/', HTTP_USER_AGENT='Googlebot/2.1')
        response = middleware(request)
        
        assert response.status_code == 200
        # Deve sincronizzare anche per spider
        assert mock_sync.called
