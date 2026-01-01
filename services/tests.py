"""
Test TDD per il modulo servizi/aree di pratica.
"""
from django.test import TestCase
from wagtail.models import Page, Site

from .models import ServiceArea, ServicesIndexPage, ServicePage


def setup_wagtail_home():
    """Helper per creare la HomePage se non esiste."""
    from home.models import HomePage
    
    if HomePage.objects.filter(slug='home').exists():
        return HomePage.objects.get(slug='home')
    
    root = Page.objects.get(slug='root')
    
    # Cerca la pagina di benvenuto di Wagtail
    try:
        welcome_page = Page.objects.get(slug='home', depth=2)
        if hasattr(welcome_page, 'homepage'):
            return welcome_page.specific
        welcome_page.delete()
    except Page.DoesNotExist:
        pass
    
    Page.fix_tree()
    root = Page.objects.get(slug='root')
    
    home = HomePage(title="Home", slug="home")
    root.add_child(instance=home)
    
    site = Site.objects.first()
    if site:
        site.root_page = home
        site.save()
    else:
        Site.objects.create(hostname='localhost', port=80, root_page=home, is_default_site=True)
    
    return home


class ServiceAreaModelTest(TestCase):
    """Test per il modello ServiceArea (snippet)."""
    
    def test_create_service_area(self):
        """Verifica che un'area di pratica possa essere creata."""
        area = ServiceArea.objects.create(
            name="Diritto Penale",
            slug="diritto-penale",
            icon="scale",
            short_description="Difesa in procedimenti penali.",
            order=1
        )
        self.assertEqual(area.name, "Diritto Penale")
        self.assertEqual(area.slug, "diritto-penale")
    
    def test_ordering_by_order_then_name(self):
        """Verifica l'ordinamento per ordine e poi nome."""
        ServiceArea.objects.create(name="Zeta", slug="zeta", short_description="", order=2)
        ServiceArea.objects.create(name="Alfa", slug="alfa", short_description="", order=1)
        ServiceArea.objects.create(name="Beta", slug="beta", short_description="", order=1)
        
        areas = list(ServiceArea.objects.all())
        self.assertEqual(areas[0].name, "Alfa")
        self.assertEqual(areas[1].name, "Beta")
        self.assertEqual(areas[2].name, "Zeta")
    
    def test_str_representation(self):
        """Verifica la rappresentazione stringa."""
        area = ServiceArea.objects.create(
            name="Privacy e GDPR", slug="privacy", short_description=""
        )
        self.assertEqual(str(area), "Privacy e GDPR")


class ServicesIndexPageTest(TestCase):
    """Test per ServicesIndexPage."""
    
    def setUp(self):
        """Setup: creo la struttura delle pagine."""
        self.home = setup_wagtail_home()
    
    def test_create_services_index_page(self):
        """Verifica che una pagina indice servizi possa essere creata."""
        services_page = ServicesIndexPage(
            title="Aree di Pratica",
            slug="aree-di-pratica",
            intro="<p>Le nostre competenze legali.</p>"
        )
        self.home.add_child(instance=services_page)
        
        self.assertEqual(services_page.title, "Aree di Pratica")
        self.assertTrue(services_page.live)
    
    def test_get_context_includes_services(self):
        """Verifica che il context includa le aree di pratica."""
        services_page = ServicesIndexPage(title="Servizi", slug="servizi")
        self.home.add_child(instance=services_page)
        
        # Pulisco le service area esistenti e ne creo una nuova
        ServiceArea.objects.all().delete()
        ServiceArea.objects.create(name="Test", slug="test", short_description="Desc")
        
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/servizi/')
        
        context = services_page.get_context(request)
        self.assertIn('services', context)
        self.assertEqual(context['services'].count(), 1)


class ServicePageTest(TestCase):
    """Test per ServicePage."""
    
    def setUp(self):
        """Setup: creo la struttura delle pagine."""
        home = setup_wagtail_home()
        
        self.services_index = ServicesIndexPage(title="Servizi", slug="servizi")
        home.add_child(instance=self.services_index)
        
        self.service_area = ServiceArea.objects.create(
            name="Diritto Penale", slug="penale", short_description="Test"
        )
    
    def test_create_service_page(self):
        """Verifica che una pagina servizio possa essere creata."""
        service_page = ServicePage(
            title="Diritto Penale",
            slug="diritto-penale",
            service_area=self.service_area,
            subtitle="Difesa penale a 360°",
            body="<p>Contenuto dettagliato.</p>"
        )
        self.services_index.add_child(instance=service_page)
        
        self.assertEqual(service_page.service_area, self.service_area)
    
    def test_service_page_parent_type(self):
        """Verifica che ServicePage possa essere figlia solo di ServicesIndexPage."""
        self.assertEqual(
            ServicePage.parent_page_types,
            ['services.ServicesIndexPage']
        )
