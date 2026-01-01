"""
Management command per creare i dati di esempio per lo Studio Legale.
Uso: python manage.py setup_demo_data
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from wagtail.models import Page, Site


class Command(BaseCommand):
    help = 'Crea la HomePage e i dati di esempio per lo Studio Legale'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sovrascrive i dati esistenti',
        )

    def handle(self, *args, **options):
        from home.models import HomePage
        from services.models import ServiceArea, ServicesIndexPage, ServicePage
        
        force = options.get('force', False)
        
        # Verifica se la HomePage esiste già
        if HomePage.objects.exists() and not force:
            self.stdout.write(
                self.style.WARNING('La HomePage esiste già. Usa --force per sovrascrivere.')
            )
            return
        
        self.stdout.write('Creazione dati di esempio per Studio Legale...')
        
        # 1. Crea/aggiorna HomePage
        self._setup_homepage()
        
        # 2. Crea le aree di pratica (ServiceArea)
        self._setup_service_areas()
        
        # 3. Crea la pagina indice servizi
        self._setup_services_page()
        
        self.stdout.write(self.style.SUCCESS('✓ Dati di esempio creati con successo!'))
        self.stdout.write('')
        self.stdout.write('Prossimi passi:')
        self.stdout.write('  1. Accedi a /admin/ per personalizzare i contenuti')
        self.stdout.write('  2. Modifica i testi della HomePage')
        self.stdout.write('  3. Aggiungi le pagine dei servizi')

    def _setup_homepage(self):
        """Crea o aggiorna la HomePage."""
        from home.models import HomePage
        
        root = Page.objects.get(slug='root')
        
        # Rimuovi la pagina di benvenuto di Wagtail se esiste
        try:
            welcome = Page.objects.get(slug='home', depth=2)
            if not hasattr(welcome.specific, 'hero_line1'):
                # È la pagina di benvenuto di Wagtail, non la nostra
                site = Site.objects.filter(root_page=welcome).first()
                welcome.delete()
                Page.fix_tree()
                root = Page.objects.get(slug='root')
        except Page.DoesNotExist:
            pass
        
        # Crea la HomePage se non esiste
        if not HomePage.objects.filter(slug='home').exists():
            homepage = HomePage(
                title="Home",
                slug="home",
                hero_line1="Studio Legale",
                hero_line2="Avv. Mario Rossi",
                hero_location="Roma",
                hero_cta_text="Prenota una consulenza",
                hero_cta_link="/prenota/",
                about_title="Chi Siamo",
                about_text="""<p>Lo Studio Legale Rossi offre assistenza legale qualificata 
                in molteplici aree del diritto, con particolare attenzione alle esigenze 
                del cliente e alla risoluzione efficace delle controversie.</p>
                <p>Con oltre 20 anni di esperienza, garantiamo professionalità, 
                riservatezza e dedizione in ogni pratica.</p>""",
            )
            root.add_child(instance=homepage)
            
            # Configura il site
            site = Site.objects.first()
            if site:
                site.root_page = homepage
                site.save()
            else:
                Site.objects.create(
                    hostname='localhost',
                    port=80,
                    root_page=homepage,
                    is_default_site=True
                )
            
            self.stdout.write(self.style.SUCCESS('  ✓ HomePage creata'))
        else:
            self.stdout.write('  - HomePage già esistente, saltata')

    def _setup_service_areas(self):
        """Crea le aree di pratica (snippet)."""
        from services.models import ServiceArea
        
        areas = [
            {
                'name': 'Diritto Penale',
                'slug': 'diritto-penale',
                'icon': 'scale',
                'short_description': 'Difesa in procedimenti penali, assistenza durante le indagini e rappresentanza in giudizio.',
                'order': 1,
            },
            {
                'name': 'Diritto di Famiglia e Successioni',
                'slug': 'famiglia-successioni',
                'icon': 'users',
                'short_description': 'Separazioni, divorzi, affidamento minori, successioni e testamenti.',
                'order': 2,
            },
            {
                'name': 'Diritto Civile',
                'slug': 'diritto-civile',
                'icon': 'file-contract',
                'short_description': 'Contratti, responsabilità civile, risarcimento danni e recupero crediti.',
                'order': 3,
            },
            {
                'name': 'Diritto del Lavoro',
                'slug': 'diritto-lavoro',
                'icon': 'briefcase',
                'short_description': 'Licenziamenti, vertenze sindacali, mobbing e infortuni sul lavoro.',
                'order': 4,
            },
            {
                'name': 'Diritto Amministrativo',
                'slug': 'diritto-amministrativo',
                'icon': 'landmark',
                'short_description': 'Ricorsi al TAR, appalti pubblici, sanzioni amministrative.',
                'order': 5,
            },
            {
                'name': 'Tutela del Consumatore',
                'slug': 'consumatori',
                'icon': 'shield-alt',
                'short_description': 'Pratiche commerciali scorrette, clausole vessatorie, garanzie.',
                'order': 6,
            },
            {
                'name': 'Recupero Crediti',
                'slug': 'recupero-crediti',
                'icon': 'coins',
                'short_description': 'Azioni legali per il recupero di crediti insoluti, decreti ingiuntivi.',
                'order': 7,
            },
            {
                'name': 'Mediazione e Negoziazione Assistita',
                'slug': 'mediazione-negoziazione',
                'icon': 'handshake',
                'short_description': 'Strumenti ADR per risolvere le controversie in modo rapido, economico e riservato.',
                'order': 8,
            },
        ]
        
        created_count = 0
        for area_data in areas:
            area, created = ServiceArea.objects.get_or_create(
                slug=area_data['slug'],
                defaults=area_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {created_count} aree di pratica create'))

    def _setup_services_page(self):
        """Crea la pagina indice dei servizi."""
        from home.models import HomePage
        from services.models import ServicesIndexPage
        
        home = HomePage.objects.filter(slug='home').first()
        if not home:
            self.stdout.write(self.style.WARNING('  - HomePage non trovata, pagina servizi saltata'))
            return
        
        if not ServicesIndexPage.objects.filter(slug='aree-pratica').exists():
            services_page = ServicesIndexPage(
                title="Aree di Pratica",
                slug="aree-pratica",
                intro="""<p>Lo Studio offre assistenza legale qualificata in diverse 
                aree del diritto. Scopri i nostri servizi e contattaci per una 
                consulenza personalizzata.</p>"""
            )
            home.add_child(instance=services_page)
            self.stdout.write(self.style.SUCCESS('  ✓ Pagina Aree di Pratica creata'))
        else:
            self.stdout.write('  - Pagina Aree di Pratica già esistente, saltata')
