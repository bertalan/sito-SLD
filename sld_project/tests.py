"""
Test TDD per verificare che tutti i link del sito funzionino.
"""
from django.test import TestCase, Client
from django.urls import reverse
from wagtail.models import Page, Site


class NavigationLinksTest(TestCase):
    """Test per verificare che tutti i link di navigazione funzionino."""
    
    def setUp(self):
        self.client = Client()
    
    def test_homepage_loads(self):
        """Verifica che la homepage si carichi."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_booking_page_loads(self):
        """Verifica che la pagina prenotazione si carichi (non 500)."""
        response = self.client.get('/prenota/')
        # Deve essere 200 o al massimo 404 se non configurato, ma MAI 500
        self.assertIn(response.status_code, [200, 302])
    
    def test_booking_slots_api(self):
        """Verifica che l'API slots funzioni."""
        from datetime import date, timedelta
        from booking.models import AvailabilityRule
        from datetime import time
        
        # Creo una regola per Lunedì
        AvailabilityRule.objects.create(
            name="Test", weekday=0, start_time=time(9, 0), end_time=time(13, 0), is_active=True
        )
        
        # Trova il prossimo Lunedì
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        response = self.client.get(f'/prenota/slots/{next_monday.isoformat()}/')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_redirects_to_login(self):
        """Verifica che l'admin reindirizzi al login."""
        response = self.client.get('/admin/')
        # Deve reindirizzare al login (302) o mostrare il login (200)
        self.assertIn(response.status_code, [200, 302])


class WagtailPagesTest(TestCase):
    """Test per verificare le pagine Wagtail."""
    
    def setUp(self):
        self.client = Client()
        
        # Setup pagine Wagtail di base
        from home.models import HomePage
        from services.models import ServicesIndexPage
        from contact.models import ContactPage
        from domiciliazioni.models import DomiciliazioniPage
        
        root = Page.objects.get(slug='root')
        
        # Trova o crea la home
        try:
            self.home = HomePage.objects.get(slug='home')
        except HomePage.DoesNotExist:
            self.home = HomePage(title="Home", slug="home")
            root.add_child(instance=self.home)
            
            # Configura il site
            site = Site.objects.first()
            if site:
                site.root_page = self.home
                site.save()
    
    def test_services_page_accessible(self):
        """Verifica che la pagina servizi sia accessibile dopo la creazione."""
        from services.models import ServicesIndexPage
        
        # Creo la pagina servizi
        services_page = ServicesIndexPage(
            title="Aree di Pratica",
            slug="aree-pratica"
        )
        self.home.add_child(instance=services_page)
        
        response = self.client.get('/aree-pratica/')
        self.assertEqual(response.status_code, 200)
    
    def test_contact_page_accessible(self):
        """Verifica che la pagina contatti sia accessibile dopo la creazione."""
        from contact.models import ContactPage
        
        contact_page = ContactPage(
            title="Contatti",
            slug="contatti",
            intro="Contattaci",
            address_lecce="Piazza Mazzini, 72",
            #address_martina="Via Salvatore Quasimodo, 12",
            phone="+39 320 7044664",
            email="test@example.com"
        )
        self.home.add_child(instance=contact_page)
        
        response = self.client.get('/contatti/')
        self.assertEqual(response.status_code, 200)
    
    def test_domiciliazioni_page_accessible(self):
        """Verifica che la pagina domiciliazioni sia accessibile dopo la creazione."""
        from domiciliazioni.models import DomiciliazioniPage
        
        domiciliazioni_page = DomiciliazioniPage(
            title="Domiciliazioni",
            slug="domiciliazioni",
            intro="Richiedi una domiciliazione"
        )
        self.home.add_child(instance=domiciliazioni_page)
        
        response = self.client.get('/domiciliazioni/')
        self.assertEqual(response.status_code, 200)


class SitemapTest(TestCase):
    """Test per la sitemap XML."""
    
    def setUp(self):
        self.client = Client()
    
    def test_sitemap_returns_xml(self):
        """Verifica che la sitemap restituisca XML valido."""
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        # Wagtail usa application/xml
        self.assertIn('xml', response['Content-Type'])
    
    def test_sitemap_contains_urls(self):
        """Verifica che la sitemap contenga URL."""
        response = self.client.get('/sitemap.xml')
        content = response.content.decode('utf-8')
        self.assertIn('<?xml', content)
        self.assertIn('<urlset', content)
        self.assertIn('<url>', content)
        self.assertIn('<loc>', content)


class RobotsTxtTest(TestCase):
    """Test per robots.txt."""
    
    def setUp(self):
        self.client = Client()
    
    def test_robots_txt_accessible(self):
        """Verifica che robots.txt sia accessibile."""
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/plain', response['Content-Type'])
    
    def test_robots_txt_content(self):
        """Verifica il contenuto di robots.txt."""
        response = self.client.get('/robots.txt')
        content = response.content.decode('utf-8')
        
        # Deve contenere le direttive base
        self.assertIn('User-agent:', content)
        self.assertIn('Allow:', content)
        self.assertIn('Sitemap:', content)
        
        # Deve bloccare admin
        self.assertIn('/admin/', content)


class CookieBannerTest(TestCase):
    """Test per il cookie banner GDPR."""
    
    def setUp(self):
        self.client = Client()
    
    def test_cookie_banner_present_in_html(self):
        """Verifica che il cookie banner sia presente nell'HTML."""
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        
        # Deve contenere il div del cookie banner
        self.assertIn('cookie-banner', content)
        self.assertIn('Accetta', content)
    
    def test_cookie_banner_has_privacy_link(self):
        """Verifica che il banner abbia link alla privacy policy."""
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        
        self.assertIn('/privacy/', content)


class GoogleAnalyticsTest(TestCase):
    """Test per Google Analytics."""
    
    def setUp(self):
        self.client = Client()
    
    def test_ga_script_present_when_configured(self):
        """Verifica che lo script GA sia presente quando configurato."""
        from django.test import override_settings
        
        with override_settings(GA4_MEASUREMENT_ID='G-TEST123'):
            response = self.client.get('/')
            content = response.content.decode('utf-8')
            
            # Lo script GA deve essere presente nel template
            self.assertIn('gtag', content)
            self.assertIn('G-TEST123', content)
    
    def test_ga_conditional_loading(self):
        """Verifica che GA sia condizionato dal consenso cookie."""
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        
        # Deve esserci la logica di verifica del consenso nel cookie banner
        self.assertIn('cookie_consent', content)
    
    def test_ga_not_loaded_without_config(self):
        """Verifica che GA non sia caricato senza configurazione."""
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        
        # Senza GA4_MEASUREMENT_ID, non deve esserci gtag
        self.assertNotIn('googletagmanager.com/gtag', content)
