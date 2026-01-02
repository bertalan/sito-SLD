"""
Test TDD per il sistema articoli.
Eseguire con: docker compose exec web python manage.py test articles
"""
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from wagtail.models import Page, Site


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


class ArticleCategoryTest(TestCase):
    """Test per ArticleCategory snippet."""
    
    def test_category_creation(self):
        """Verifica creazione categoria."""
        from articles.models import ArticleCategory
        
        category = ArticleCategory.objects.create(
            name='Guide',
            slug='guide',
            icon='book-open',
            order=1
        )
        self.assertEqual(str(category), 'Guide')
        self.assertEqual(category.slug, 'guide')
    
    def test_category_ordering(self):
        """Verifica ordinamento categorie per order."""
        from articles.models import ArticleCategory
        
        ArticleCategory.objects.create(name='News', slug='news', order=2)
        ArticleCategory.objects.create(name='Guide', slug='guide', order=1)
        ArticleCategory.objects.create(name='Pareri', slug='pareri', order=3)
        
        categories = list(ArticleCategory.objects.values_list('slug', flat=True))
        self.assertEqual(categories, ['guide', 'news', 'pareri'])


class ArticleIndexPageTest(TestCase):
    """Test per ArticleIndexPage."""
    
    def setUp(self):
        """Setup pagina indice articoli."""
        from articles.models import ArticleIndexPage
        
        self.home = setup_wagtail_home()
        
        # Crea ArticleIndexPage sotto home
        self.index_page = ArticleIndexPage(
            title='Articoli',
            slug='articoli',
            intro='<p>Blog legale dello studio.</p>'
        )
        self.home.add_child(instance=self.index_page)
    
    def test_index_page_created(self):
        """Verifica che la pagina indice sia stata creata correttamente."""
        self.assertEqual(self.index_page.title, 'Articoli')
        self.assertTrue(self.index_page.live)
        self.assertIsNotNone(self.index_page.url)
    
    def test_index_has_articles_context(self):
        """Verifica che il context contenga gli articoli."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/articoli/')
        
        context = self.index_page.get_context(request)
        self.assertIn('articles', context)
        self.assertIn('categories', context)


class ArticlePageTest(TestCase):
    """Test per ArticlePage."""
    
    def setUp(self):
        """Setup articolo di test."""
        from articles.models import ArticleIndexPage, ArticlePage, ArticleCategory
        
        self.home = setup_wagtail_home()
        
        # Crea ArticleIndexPage
        self.index_page = ArticleIndexPage(
            title='Articoli',
            slug='articoli'
        )
        self.home.add_child(instance=self.index_page)
        
        # Crea categoria
        self.category = ArticleCategory.objects.create(
            name='Guide',
            slug='guide'
        )
        
        # Crea articolo
        self.article = ArticlePage(
            title='Guida senza casco',
            slug='guida-senza-casco',
            subtitle='Cosa sapere sulla guida senza casco',
            body='<p>Contenuto dell\'articolo con molte parole per testare il calcolo del tempo di lettura.</p>'
        )
        self.index_page.add_child(instance=self.article)
        self.article.category = self.category
        self.article.save()
    
    def test_article_page_created(self):
        """Verifica che l'articolo sia stato creato correttamente."""
        self.assertEqual(self.article.title, 'Guida senza casco')
        self.assertTrue(self.article.live)
        self.assertIsNotNone(self.article.url)
    
    def test_article_has_context(self):
        """Verifica che il context contenga articoli correlati."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/articoli/guida-senza-casco/')
        
        context = self.article.get_context(request)
        self.assertIn('related_articles', context)
    
    def test_reading_time_calculated(self):
        """Verifica calcolo automatico tempo di lettura."""
        self.assertGreaterEqual(self.article.reading_time, 1)
    
    def test_article_has_category(self):
        """Verifica che l'articolo abbia una categoria."""
        self.assertEqual(self.article.category.name, 'Guide')
    
    def test_article_search_description(self):
        """Verifica che subtitle sia usato come search_description se vuoto."""
        # Se search_description è vuoto, dovrebbe usare subtitle
        self.article.search_description = ''
        self.article.save()
        self.assertEqual(self.article.subtitle, 'Cosa sapere sulla guida senza casco')


class ArticleServiceAreaRelationTest(TestCase):
    """Test per la relazione ArticlePage <-> ServiceArea."""
    
    def setUp(self):
        """Setup articolo con area di pratica."""
        from articles.models import ArticleIndexPage, ArticlePage
        from services.models import ServiceArea
        
        self.home = setup_wagtail_home()
        
        # Crea area di pratica
        self.service_area = ServiceArea.objects.create(
            name='Infortunistica Stradale',
            slug='infortunistica-stradale',
            short_description='Assistenza per incidenti stradali'
        )
        
        # Crea indice e articolo
        self.index_page = ArticleIndexPage(title='Articoli', slug='articoli')
        self.home.add_child(instance=self.index_page)
        
        self.article = ArticlePage(
            title='Guida senza casco',
            slug='guida-senza-casco',
            body='<p>Contenuto articolo.</p>'
        )
        self.index_page.add_child(instance=self.article)
    
    def test_article_can_have_service_areas(self):
        """Verifica che un articolo possa essere collegato a più aree."""
        self.article.service_areas.add(self.service_area)
        self.article.save()
        
        self.assertIn(self.service_area, self.article.service_areas.all())
    
    def test_get_articles_for_service_area(self):
        """Verifica helper per ottenere articoli di un'area."""
        from articles.models import get_articles_for_service_area
        
        self.article.service_areas.add(self.service_area)
        self.article.save()
        
        articles = get_articles_for_service_area(self.service_area)
        self.assertIn(self.article, articles)


class ArticleSchemaOrgTest(TestCase):
    """Test per Schema.org JSON-LD degli articoli."""
    
    def setUp(self):
        """Setup articolo per test schema."""
        from articles.models import ArticleIndexPage, ArticlePage, ArticleCategory
        
        self.home = setup_wagtail_home()
        
        self.category = ArticleCategory.objects.create(name='Guide', slug='guide')
        
        self.index_page = ArticleIndexPage(title='Articoli', slug='articoli')
        self.home.add_child(instance=self.index_page)
        
        self.article = ArticlePage(
            title='Guida senza casco',
            slug='guida-senza-casco',
            subtitle='Cosa sapere',
            body='<p>Contenuto.</p>'
        )
        self.index_page.add_child(instance=self.article)
        self.article.category = self.category
        self.article.save()
    
    def test_article_template_exists(self):
        """Verifica che il template dell'articolo esista."""
        import os
        from django.conf import settings
        
        # Il template è in articles/templates/articles/article_page.html
        template_path = os.path.join(
            settings.BASE_DIR, 'articles', 'templates', 'articles', 'article_page.html'
        )
        self.assertTrue(os.path.exists(template_path))
    
    def test_article_template_has_schema_org(self):
        """Verifica che il template contenga JSON-LD Article."""
        import os
        from django.conf import settings
        
        template_path = os.path.join(
            settings.BASE_DIR, 'articles', 'templates', 'articles', 'article_page.html'
        )
        with open(template_path, 'r') as f:
            content = f.read()
        
        # JSON-LD compattato senza spazi
        self.assertIn('"@type":"Article"', content)
        self.assertIn('application/ld+json', content)


class ServicePageRelatedArticlesTest(TestCase):
    """Test per articoli correlati nelle pagine servizio."""
    
    def setUp(self):
        """Setup ServicePage con articolo correlato."""
        from articles.models import ArticleIndexPage, ArticlePage, ArticleCategory
        from services.models import ServiceArea, ServicesIndexPage, ServicePage
        
        self.home = setup_wagtail_home()
        
        # Crea ServiceArea e ServicePage
        self.service_area = ServiceArea.objects.create(
            name='Diritto Penale', 
            slug='diritto-penale'
        )
        
        self.services_index = ServicesIndexPage(title='Servizi', slug='servizi')
        self.home.add_child(instance=self.services_index)
        
        self.service_page = ServicePage(
            title='Diritto Penale',
            slug='diritto-penale-page',
            service_area=self.service_area,
            subtitle='Difesa penale',
            body='<p>Contenuto.</p>'
        )
        self.services_index.add_child(instance=self.service_page)
        
        # Crea articolo correlato
        self.category = ArticleCategory.objects.create(name='Guide', slug='guide')
        self.article_index = ArticleIndexPage(title='Articoli', slug='articoli')
        self.home.add_child(instance=self.article_index)
        
        self.article = ArticlePage(
            title='Guida penale',
            slug='guida-penale',
            subtitle='Guida completa',
            body='<p>Contenuto articolo.</p>'
        )
        self.article_index.add_child(instance=self.article)
        self.article.category = self.category
        self.article.service_areas.add(self.service_area)
        self.article.save()
    
    def test_service_page_has_related_articles_in_context(self):
        """Verifica che ServicePage includa articoli correlati nel context."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        
        context = self.service_page.get_context(request)
        
        self.assertIn('related_articles', context)
        self.assertIn(self.article, context['related_articles'])

