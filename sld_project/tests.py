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
            address_martina="Via Salvatore Quasimodo, 12",
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
