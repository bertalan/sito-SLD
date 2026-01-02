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
        
        # 0. Crea SiteSettings
        self._setup_site_settings()
        
        # 1. Crea/aggiorna HomePage
        self._setup_homepage()
        
        # 2. Crea le aree di pratica (ServiceArea)
        self._setup_service_areas()
        
        # 3. Crea la pagina indice servizi
        self._setup_services_page()
        
        # 4. Crea pagine aggiuntive
        self._setup_contact_page()
        self._setup_domiciliazioni_page()
        self._setup_booking_page()
        
        self.stdout.write(self.style.SUCCESS('✓ Dati di esempio creati con successo!'))
        self.stdout.write('')
        self.stdout.write('Prossimi passi:')
        self.stdout.write('  1. Accedi a /admin/ per personalizzare i contenuti')
        self.stdout.write('  2. Vai su Impostazioni > Impostazioni Studio per configurare i dati')
        self.stdout.write('  3. Modifica i testi della HomePage')

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
                hero_line1="ASSISTENZA LEGALE",
                hero_line2="PER UNA TUTELA",
                hero_line3="DI ELEVATA EFFICACIA",
                hero_line4="E COMPETENZA",
                hero_subtitle="AVVOCATO",
                hero_accent="GIUSTIZIA.",
                hero_location="• Roma",
                about_title="LO STUDIO",
                about_text="""<p>Lo Studio Legale offre assistenza legale qualificata 
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

    def _setup_site_settings(self):
        """Crea le impostazioni dello studio."""
        from sld_project.models import SiteSettings
        from wagtail.models import Site
        
        site = Site.objects.filter(is_default_site=True).first()
        if not site:
            # Se non c'è un site, verrà creato dopo con la homepage
            self.stdout.write('  - Site non ancora creato, SiteSettings verrà configurato dopo')
            return
        
        settings, created = SiteSettings.objects.get_or_create(site=site)
        if created:
            settings.studio_name = "Studio Legale"
            settings.lawyer_name = "Avv. Mario Rossi"
            settings.email = "info@example.com"
            settings.email_pec = "avvocato@pec.it"
            settings.phone = "+39 06 12345678"
            settings.address = "Via Roma, 1 - 00100 Roma"
            settings.city = "Roma"
            settings.maps_lat = 41.902782
            settings.maps_lng = 12.496366
            settings.maps_url = "https://maps.apple.com/?daddr=41.9028,12.4964"
            settings.website = "www.example.com"
            settings.jitsi_room_prefix = "StudioLegale"
            settings.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Impostazioni Studio create'))
        else:
            self.stdout.write('  - Impostazioni Studio già esistenti, saltate')

    def _setup_contact_page(self):
        """Crea la pagina contatti."""
        from home.models import HomePage
        from contact.models import ContactPage
        
        home = HomePage.objects.filter(slug='home').first()
        if not home:
            return
        
        if not ContactPage.objects.filter(slug='contatti').exists():
            contact_page = ContactPage(
                title="Contatti",
                slug="contatti",
                intro="<p>Contattaci per una consulenza o per maggiori informazioni sui nostri servizi.</p>",
                thank_you_text="<p>Grazie per averci contattato! Ti risponderemo al più presto.</p>",
            )
            home.add_child(instance=contact_page)
            self.stdout.write(self.style.SUCCESS('  ✓ Pagina Contatti creata'))
        else:
            self.stdout.write('  - Pagina Contatti già esistente, saltata')

    def _setup_domiciliazioni_page(self):
        """Crea la pagina domiciliazioni."""
        from home.models import HomePage
        from domiciliazioni.models import DomiciliazioniPage
        
        home = HomePage.objects.filter(slug='home').first()
        if not home:
            return
        
        if not DomiciliazioniPage.objects.filter(slug='domiciliazioni').exists():
            page = DomiciliazioniPage(
                title='Domiciliazioni',
                slug='domiciliazioni',
                intro='<p>Servizio di domiciliazione legale per colleghi avvocati presso i Tribunali di Roma.</p>',
                service_description='<p>Offriamo un servizio professionale di domiciliazione legale per udienze civili, penali, del lavoro e amministrative presso il Tribunale di Roma, la Corte d\'Appello, il Giudice di Pace, il TAR Lazio e l\'ufficio UNEP.</p>',
                thank_you_text='<p>Grazie per la richiesta di domiciliazione. La contatteremo al più presto per confermare la disponibilità.</p>',
                tribunali='Tribunale di Roma\nCorte d\'Appello di Roma\nGiudice di Pace di Roma\nTAR Lazio\nUfficio UNEP di Roma',
                to_address='info@example.com',
                from_address='noreply@example.com',
                subject='Nuova richiesta domiciliazione',
            )
            home.add_child(instance=page)
            page.save_revision().publish()
            self.stdout.write(self.style.SUCCESS('  ✓ Pagina Domiciliazioni creata'))
        else:
            self.stdout.write('  - Pagina Domiciliazioni già esistente, saltata')

    def _setup_booking_page(self):
        """Crea le regole di disponibilità per le prenotazioni."""
        from booking.models import AvailabilityRule
        from datetime import time
        
        # Crea regole di disponibilità default (Lun-Ven 9-13, 15-18)
        if not AvailabilityRule.objects.exists():
            for day in range(5):  # 0=Lunedì, 4=Venerdì
                AvailabilityRule.objects.create(
                    weekday=day,
                    start_time=time(9, 0),
                    end_time=time(13, 0),
                    is_active=True,
                    name=f'Mattina {["Lun", "Mar", "Mer", "Gio", "Ven"][day]}'
                )
                AvailabilityRule.objects.create(
                    weekday=day,
                    start_time=time(15, 0),
                    end_time=time(18, 0),
                    is_active=True,
                    name=f'Pomeriggio {["Lun", "Mar", "Mer", "Gio", "Ven"][day]}'
                )
            self.stdout.write(self.style.SUCCESS('  ✓ Regole disponibilità create (Lun-Ven 9-13, 15-18)'))
        else:
            self.stdout.write('  - Regole disponibilità già esistenti, saltate')
        
        # Crea appuntamenti demo
        self._setup_demo_appointments()
        
        # Crea domiciliazioni demo
        self._setup_demo_domiciliazioni()

    def _next_workday(self, from_date, days_ahead=1):
        """Trova il prossimo giorno lavorativo (salta weekend)."""
        from datetime import timedelta
        result = from_date + timedelta(days=days_ahead)
        while result.weekday() >= 5:  # Sabato=5, Domenica=6
            result += timedelta(days=1)
        return result

    def _setup_demo_appointments(self):
        """Crea appuntamenti demo con date relative."""
        from booking.models import Appointment
        from datetime import date, time
        
        # Salta se esistono già appuntamenti
        if Appointment.objects.exists():
            self.stdout.write('  - Appuntamenti demo già esistenti, saltati')
            return
        
        today = date.today()
        
        # Appuntamento 1: domani (prossimo lun-ven) alle 10:00 - in presenza
        app1_date = self._next_workday(today, 1)
        Appointment.objects.create(
            first_name='Marco',
            last_name='Bianchi',
            email='demo.civile@example.com',
            phone='+39 333 1234567',
            notes='Consulenza per contratto di locazione - DEMO',
            consultation_type='in_person',
            date=app1_date,
            time=time(10, 0),
            slot_count=1,
            status='confirmed',
            payment_method='stripe',
            amount_paid=60.00,
        )
        
        # Appuntamento 2: dopodomani (prossimo lun-ven) alle 15:30 - videochiamata
        app2_date = self._next_workday(today, 2)
        Appointment.objects.create(
            first_name='Laura',
            last_name='Verdi',
            email='demo.penale@example.com',
            phone='+39 339 7654321',
            notes='Consulenza penale urgente - DEMO',
            consultation_type='video',
            date=app2_date,
            time=time(15, 30),
            slot_count=2,  # 1 ora
            status='confirmed',
            payment_method='paypal',
            amount_paid=120.00,
        )
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 2 appuntamenti demo creati ({app1_date}, {app2_date})'))

    def _setup_demo_domiciliazioni(self):
        """Crea domiciliazioni demo con date relative."""
        from domiciliazioni.models import DomiciliazioniSubmission, DomiciliazioniPage
        from datetime import date, time
        
        # Salta se esistono già
        if DomiciliazioniSubmission.objects.exists():
            self.stdout.write('  - Domiciliazioni demo già esistenti, saltate')
            return
        
        # Trova la pagina domiciliazioni
        page = DomiciliazioniPage.objects.first()
        
        today = date.today()
        
        # Domiciliazione 1: tra 3 giorni lavorativi - udienza civile
        dom1_date = self._next_workday(today, 3)
        DomiciliazioniSubmission.objects.create(
            page=page,
            nome_avvocato='Avv. Giuseppe Neri',
            email='demo.domiciliazione1@example.com',
            telefono='+39 06 5551234',
            ordine_appartenenza='Ordine degli Avvocati di Milano',
            tribunale='roma',
            sezione='Sezione Civile',
            giudice='Dott. Rossi',
            tipo_udienza='civile',
            numero_rg='1234/2026',
            parti_causa='Rossi Mario c/ Verdi Luigi',
            data_udienza=dom1_date,
            ora_udienza=time(9, 30),
            attivita_richieste='Mera comparizione e richiesta rinvio per trattative in corso',
            note='Prima udienza - DEMO',
            status='accepted',
        )
        
        # Domiciliazione 2: tra 5 giorni lavorativi - TAR Lazio
        dom2_date = self._next_workday(today, 5)
        DomiciliazioniSubmission.objects.create(
            page=page,
            nome_avvocato='Avv. Maria Bianchi',
            email='demo.domiciliazione2@example.com',
            telefono='+39 02 5559876',
            ordine_appartenenza='Ordine degli Avvocati di Napoli',
            tribunale='tar',
            sezione='Sezione I',
            giudice='',
            tipo_udienza='civile',
            numero_rg='5678/2026',
            parti_causa='Comune di Roma c/ Impresa Edile Srl',
            data_udienza=dom2_date,
            ora_udienza=time(11, 0),
            attivita_richieste='Comparizione e discussione orale. Depositare memoria difensiva allegata.',
            note='Ricorso appalto pubblico - DEMO',
            status='pending',
        )
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 2 domiciliazioni demo create ({dom1_date}, {dom2_date})'))

