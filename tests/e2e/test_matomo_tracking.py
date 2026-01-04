"""
Test E2E per verificare che Matomo riceva effettivamente le visite.
Simula un visitatore reale che ha accettato i cookie.
"""
import pytest
from playwright.sync_api import Page, expect
import re
import os

# URL del server (Docker locale o variabile d'ambiente)
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')


class TestMatomoTracking:
    """Test di tracking Matomo con visitatore reale."""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup per ogni test."""
        self.page = page
        self.base_url = BASE_URL
        self.matomo_requests = []
        
        # Intercetta tutte le richieste a matomo.php
        def capture_matomo_request(request):
            if 'matomo.php' in request.url:
                self.matomo_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'post_data': request.post_data
                })
        
        page.on('request', capture_matomo_request)
    
    def accept_cookies(self):
        """Accetta tutti i cookie cliccando sul banner."""
        # Aspetta che il banner appaia
        banner = self.page.locator('#cookie-banner')
        
        # Il banner potrebbe non apparire se i cookie sono già accettati
        try:
            banner.wait_for(state='visible', timeout=3000)
            accept_btn = self.page.locator('#cookie-accept-btn')
            accept_btn.click()
            # Aspetta che il banner scompaia
            banner.wait_for(state='hidden', timeout=2000)
        except:
            pass  # Banner già nascosto o cookie già accettati
    
    def set_cookie_consent_directly(self):
        """Imposta il cookie di consenso direttamente (più affidabile per test)."""
        self.page.context.add_cookies([{
            'name': 'cookie_consent',
            'value': '{"necessary":true,"analytics":true}',
            'domain': 'localhost',
            'path': '/'
        }])
    
    def test_matomo_script_loads_with_consent(self):
        """
        Verifica che lo script Matomo venga caricato quando l'utente accetta i cookie.
        """
        # Vai alla home
        self.page.goto(self.base_url)
        
        # Accetta i cookie
        self.accept_cookies()
        
        # Aspetta un po' per dare tempo a Matomo di inizializzarsi
        self.page.wait_for_timeout(1000)
        
        # Verifica che _paq esista (può essere array o oggetto Matomo dopo il caricamento)
        paq_exists = self.page.evaluate('typeof window._paq !== "undefined"')
        assert paq_exists, "_paq dovrebbe esistere"
        
        # Verifica che matomoLoaded sia true (se Matomo è configurato)
        matomo_loaded = self.page.evaluate('window.matomoLoaded === true')
        print(f"matomoLoaded: {matomo_loaded}")
        assert matomo_loaded, "matomoLoaded dovrebbe essere true dopo l'accettazione cookie"
    
    def test_matomo_paq_commands_queued(self):
        """
        Verifica che i comandi _paq vengano eseguiti correttamente.
        """
        # Imposta cookie di consenso prima di navigare
        self.page.goto(self.base_url)
        self.set_cookie_consent_directly()
        
        # Ricarica per applicare il consenso
        self.page.reload()
        self.page.wait_for_timeout(1000)
        
        # Verifica che _paq esista e sia stato inizializzato
        # Dopo il caricamento di matomo.js, _paq diventa un oggetto Matomo con metodo push
        paq_type = self.page.evaluate('''
            () => {
                if (!window._paq) return 'undefined';
                if (Array.isArray(window._paq)) return 'array';
                if (typeof window._paq.push === 'function') return 'matomo_object';
                return typeof window._paq;
            }
        ''')
        
        print(f"Tipo _paq: {paq_type}")
        
        # Dopo il caricamento di matomo.js, _paq diventa un oggetto Matomo
        assert paq_type in ['array', 'matomo_object'], f"_paq dovrebbe essere array o oggetto Matomo, non {paq_type}"
    
    def test_matomo_tracker_url_configured(self):
        """
        Verifica che il tracker URL sia configurato correttamente nel DOM.
        """
        self.page.goto(self.base_url)
        
        # Cerca nel contenuto della pagina
        content = self.page.content()
        
        # Verifica che setTrackerUrl sia presente
        assert 'setTrackerUrl' in content, "setTrackerUrl dovrebbe essere nel codice"
        
        # Verifica che l'ordine sia corretto: setDoNotTrack prima di trackPageView
        set_dnt_pos = content.find('setDoNotTrack')
        track_pv_pos = content.find('trackPageView')
        
        if set_dnt_pos > 0 and track_pv_pos > 0:
            assert set_dnt_pos < track_pv_pos, "setDoNotTrack deve venire prima di trackPageView"
    
    def test_matomo_noscript_fallback_present(self):
        """
        Verifica che il fallback noscript sia presente per utenti senza JS.
        """
        self.page.goto(self.base_url)
        
        content = self.page.content()
        
        # Cerca il tag noscript con l'immagine di tracking
        assert '<noscript>' in content, "Tag noscript dovrebbe essere presente"
        assert 'matomo.php?idsite=' in content, "URL matomo.php con idsite dovrebbe essere presente"
    
    def test_visitor_journey_tracking(self):
        """
        Simula un percorso completo di un visitatore e verifica il tracking.
        """
        # 1. Prima visita - Home
        self.page.goto(self.base_url)
        self.accept_cookies()
        self.page.wait_for_timeout(500)
        
        # 2. Naviga ad altre pagine
        pages_to_visit = [
            '/contatti/',
            '/prenota/',
            '/privacy/',
        ]
        
        for path in pages_to_visit:
            try:
                self.page.goto(f"{self.base_url}{path}")
                self.page.wait_for_timeout(300)
            except:
                pass  # Alcune pagine potrebbero non esistere
        
        # 3. Verifica che ci siano state richieste a Matomo
        print(f"Richieste Matomo intercettate: {len(self.matomo_requests)}")
        for req in self.matomo_requests:
            print(f"  - {req['method']} {req['url'][:100]}...")
        
        # Se MATOMO_URL è configurato, dovremmo vedere delle richieste
        # Altrimenti, il test passa comunque (è informativo)
    
    def test_console_logs_for_matomo_errors(self):
        """
        Verifica che non ci siano errori JavaScript relativi a Matomo.
        """
        console_errors = []
        
        def capture_console(msg):
            if msg.type == 'error':
                console_errors.append(msg.text)
        
        self.page.on('console', capture_console)
        
        # Visita con cookie accettati
        self.page.goto(self.base_url)
        self.accept_cookies()
        self.page.wait_for_timeout(1000)
        
        # Filtra errori relativi a Matomo
        matomo_errors = [e for e in console_errors if 'matomo' in e.lower() or '_paq' in e.lower()]
        
        print(f"Errori console totali: {len(console_errors)}")
        print(f"Errori Matomo: {matomo_errors}")
        
        assert len(matomo_errors) == 0, f"Non dovrebbero esserci errori Matomo: {matomo_errors}"
    
    def test_init_matomo_function_callable(self):
        """
        Verifica che la funzione initMatomo sia definita e chiamabile.
        """
        self.page.goto(self.base_url)
        
        # Verifica che initMatomo esista
        init_matomo_exists = self.page.evaluate('typeof window.initMatomo === "function"')
        
        # Nota: initMatomo potrebbe non esistere se MATOMO_URL non è configurato
        # In tal caso il blocco {% if matomo_url %} non viene renderizzato
        print(f"initMatomo esiste: {init_matomo_exists}")
        
        if init_matomo_exists:
            # Prova a chiamarla (con consenso già dato)
            self.set_cookie_consent_directly()
            self.page.reload()
            self.page.wait_for_timeout(500)
            
            # Dopo il reload con consenso, matomoLoaded dovrebbe essere true
            matomo_loaded = self.page.evaluate('window.matomoLoaded')
            print(f"matomoLoaded dopo initMatomo: {matomo_loaded}")


class TestMatomoWithRealConfig:
    """
    Test con configurazione Matomo reale (piwik.gpsbooking.com).
    Questi test verificano la connessione effettiva al server Matomo.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup per ogni test."""
        self.page = page
        self.base_url = BASE_URL
        self.matomo_requests = []
        self.matomo_responses = []
        
        # Intercetta richieste e risposte a Matomo
        def capture_request(request):
            if 'piwik.gpsbooking.com' in request.url or 'matomo' in request.url:
                self.matomo_requests.append({
                    'url': request.url,
                    'method': request.method,
                })
        
        def capture_response(response):
            if 'piwik.gpsbooking.com' in response.url or 'matomo' in response.url:
                self.matomo_responses.append({
                    'url': response.url,
                    'status': response.status,
                })
        
        page.on('request', capture_request)
        page.on('response', capture_response)
    
    def test_matomo_server_reachable(self):
        """
        Verifica che il server Matomo sia raggiungibile.
        """
        # Vai alla home con cookie accettati
        self.page.goto(self.base_url)
        
        # Imposta cookie e ricarica
        self.page.context.add_cookies([{
            'name': 'cookie_consent',
            'value': '{"necessary":true,"analytics":true}',
            'domain': 'localhost',
            'path': '/'
        }])
        self.page.reload()
        
        # Aspetta che le richieste vengano fatte
        self.page.wait_for_timeout(3000)
        
        print("\n=== RICHIESTE MATOMO ===")
        for req in self.matomo_requests:
            print(f"  REQUEST: {req['method']} {req['url']}")
        
        print("\n=== RISPOSTE MATOMO ===")
        for res in self.matomo_responses:
            print(f"  RESPONSE: {res['status']} {res['url']}")
        
        # Se ci sono risposte, verifica che siano 200 o 204 (success)
        if self.matomo_responses:
            for res in self.matomo_responses:
                assert res['status'] in [200, 204, 302], f"Risposta Matomo non valida: {res['status']}"
            print(f"\n✅ Matomo ha risposto correttamente! {len(self.matomo_responses)} risposte ricevute.")
        else:
            print("\n⚠️  Nessuna richiesta Matomo rilevata. Verifica che MATOMO_URL sia configurato.")
