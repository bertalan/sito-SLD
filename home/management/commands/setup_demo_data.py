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
        
        # 2. Crea le aree di attività (ServiceArea)
        self._setup_service_areas()
        
        # 3. Crea la pagina indice servizi
        self._setup_services_page()
        
        # 4. Crea pagine aggiuntive
        self._setup_contact_page()
        self._setup_domiciliazioni_page()
        self._setup_booking_page()
        
        # 5. Crea articoli demo
        self._setup_demo_articles()
        
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
        """Crea le aree di attività (snippet)."""
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
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {created_count} aree di attività create'))

    def _setup_services_page(self):
        """Crea la pagina indice dei servizi e le pagine delle singole aree."""
        from home.models import HomePage
        from services.models import ServiceArea, ServicesIndexPage, ServicePage
        
        home = HomePage.objects.filter(slug='home').first()
        if not home:
            self.stdout.write(self.style.WARNING('  - HomePage non trovata, pagina servizi saltata'))
            return
        
        # Crea la pagina indice
        if not ServicesIndexPage.objects.filter(slug='aree-attivita').exists():
            services_page = ServicesIndexPage(
                title="Aree di Attività",
                slug="aree-attivita",
                intro="""<p>Lo Studio offre assistenza legale qualificata in diverse 
                aree del diritto. Scopri i nostri servizi e contattaci per una 
                consulenza personalizzata.</p>"""
            )
            home.add_child(instance=services_page)
            self.stdout.write(self.style.SUCCESS('  ✓ Pagina Aree di Attività creata'))
        else:
            services_page = ServicesIndexPage.objects.filter(slug='aree-attivita').first()
            self.stdout.write('  - Pagina Aree di Attività già esistente, saltata')
        
        # Crea le pagine delle singole aree di attività
        self._setup_service_pages(services_page)

    def _setup_service_pages(self, services_index):
        """Crea le pagine delle singole aree di attività con contenuti."""
        from services.models import ServiceArea, ServicePage
        
        if not services_index:
            return
        
        # Contenuti per ogni area di pratica
        contenuti = {
            'diritto-penale': {
                'subtitle': 'Difesa penale a tutela dei tuoi diritti',
                'body': """<p>La difesa in ambito penale richiede competenza, tempestività e una profonda conoscenza delle dinamiche processuali. Lo Studio offre assistenza in ogni fase del procedimento, dall'indagine preliminare fino all'eventuale appello, garantendo una strategia difensiva personalizzata.</p>
<p>Ci occupiamo di reati contro la persona, contro il patrimonio, reati stradali e violazioni in materia di sicurezza sul lavoro. Ogni caso viene analizzato con attenzione per individuare le migliori soluzioni, privilegiando quando possibile percorsi alternativi alla detenzione.</p>
<h3>Ambiti di intervento</h3>
<ul>
<li>Reati contro la persona e contro il patrimonio</li>
<li>Reati stradali e guida in stato di ebbrezza</li>
<li>Reati in materia di sicurezza sul lavoro</li>
<li>Misure cautelari e alternative alla detenzione</li>
<li>Procedimenti davanti al Tribunale e alla Corte d'Appello</li>
</ul>"""
            },
            'famiglia-successioni': {
                'subtitle': 'Accompagniamo le famiglie nei momenti più delicati',
                'body': """<p>Le questioni familiari richiedono sensibilità oltre che competenza tecnica. Lo Studio assiste i clienti in separazioni, divorzi, affidamento dei figli e regolamentazione dei rapporti patrimoniali tra coniugi, cercando sempre soluzioni consensuali prima del contenzioso.</p>
<p>In materia successoria, offriamo consulenza per la pianificazione ereditaria, la redazione di testamenti e la gestione delle divisioni ereditarie, tutelando gli interessi del cliente nel rispetto delle volontà del defunto.</p>
<h3>Ambiti di intervento</h3>
<ul>
<li>Separazioni e divorzi consensuali e giudiziali</li>
<li>Affidamento e mantenimento dei figli</li>
<li>Modifica delle condizioni di separazione e divorzio</li>
<li>Successioni e divisioni ereditarie</li>
<li>Testamenti e pianificazione successoria</li>
</ul>"""
            },
            'diritto-civile': {
                'subtitle': 'Tutela dei diritti nella vita quotidiana',
                'body': """<p>Il diritto civile permea ogni aspetto della vita: dai contratti alle responsabilità, dalla proprietà ai rapporti di vicinato. Lo Studio offre consulenza e assistenza in controversie contrattuali, risarcimento danni, diritti reali e obbligazioni.</p>
<p>Affrontiamo ogni questione con un approccio pragmatico, valutando costi e benefici di ogni azione e privilegiando la risoluzione stragiudiziale quando conveniente per il cliente.</p>
<h3>Ambiti di intervento</h3>
<ul>
<li>Controversie contrattuali e inadempimenti</li>
<li>Risarcimento danni da responsabilità civile</li>
<li>Diritti reali e controversie di vicinato</li>
<li>Locazioni e sfratti</li>
<li>Esecuzioni immobiliari e mobiliari</li>
</ul>"""
            },
            'diritto-lavoro': {
                'subtitle': 'A fianco di lavoratori e imprese',
                'body': """<p>Lo Studio assiste sia lavoratori che datori di lavoro nelle questioni giuslavoristiche: licenziamenti, impugnazione di sanzioni disciplinari, mobbing, differenze retributive e inquadramento contrattuale.</p>
<p>Per le imprese, offriamo consulenza nella gestione del personale, nella redazione di contratti e regolamenti aziendali, e nell'assistenza durante le procedure di riduzione del personale.</p>
<h3>Ambiti di intervento</h3>
<ul>
<li>Impugnazione licenziamenti e sanzioni disciplinari</li>
<li>Differenze retributive e inquadramento</li>
<li>Mobbing e demansionamento</li>
<li>Consulenza contrattualistica per imprese</li>
<li>Procedure di riduzione del personale</li>
</ul>"""
            },
            'diritto-amministrativo': {
                'subtitle': 'Dialogo efficace con la Pubblica Amministrazione',
                'body': """<p>I rapporti con gli enti pubblici possono generare contenziosi complessi. Lo Studio assiste cittadini e imprese nei ricorsi contro provvedimenti amministrativi, nelle procedure di accesso agli atti e nelle controversie con Comuni, Regioni e altri enti.</p>
<p>Particolare attenzione viene dedicata alle autorizzazioni, concessioni e alle problematiche legate all'urbanistica e all'edilizia.</p>
<h3>Ambiti di intervento</h3>
<ul>
<li>Ricorsi al TAR e al Consiglio di Stato</li>
<li>Accesso agli atti e trasparenza amministrativa</li>
<li>Autorizzazioni e concessioni</li>
<li>Urbanistica ed edilizia</li>
<li>Sanzioni amministrative</li>
</ul>"""
            },
            'consumatori': {
                'subtitle': 'I tuoi diritti nelle transazioni quotidiane',
                'body': """<p>Acquisti online difettosi, clausole vessatorie, pratiche commerciali scorrette: lo Studio difende i consumatori nelle controversie con venditori, fornitori di servizi e istituti finanziari.</p>
<p>Assistiamo i clienti nelle procedure di reclamo, nelle conciliazioni paritetiche e, quando necessario, nel contenzioso giudiziale per ottenere rimborsi e risarcimenti.</p>
<h3>Ambiti di intervento</h3>
<ul>
<li>Prodotti difettosi e garanzie</li>
<li>Clausole vessatorie nei contratti</li>
<li>Pratiche commerciali scorrette</li>
<li>Controversie con istituti finanziari</li>
<li>Conciliazioni paritetiche e ADR</li>
</ul>"""
            },
            'recupero-crediti': {
                'subtitle': 'Protezione del tuo patrimonio creditizio',
                'body': """<p>Un credito insoluto rappresenta un danno economico e un impegno gestionale. Lo Studio offre un servizio completo di recupero crediti, dalla diffida stragiudiziale all'azione esecutiva.</p>
<p>Valutiamo preventivamente la solvibilità del debitore per evitare azioni infruttuose, e proponiamo soluzioni transattive quando risultano più vantaggiose rispetto al contenzioso.</p>
<h3>Ambiti di intervento</h3>
<ul>
<li>Diffide e solleciti di pagamento</li>
<li>Decreti ingiuntivi</li>
<li>Pignoramenti mobiliari e immobiliari</li>
<li>Pignoramento presso terzi</li>
<li>Accordi transattivi e piani di rientro</li>
</ul>"""
            },
            'mediazione-negoziazione': {
                'subtitle': 'Risolvere le controversie senza andare in tribunale',
                'body': """<p>Non tutte le dispute richiedono un processo. Lo Studio accompagna i clienti nei procedimenti di mediazione civile e commerciale e nelle negoziazioni assistite, strumenti che permettono di raggiungere accordi in tempi brevi e con costi contenuti.</p>
<p>L'obiettivo è trovare soluzioni condivise che preservino, quando possibile, i rapporti tra le parti.</p>
<h3>Ambiti di intervento</h3>
<ul>
<li>Mediazione civile e commerciale</li>
<li>Negoziazione assistita</li>
<li>Arbitrati</li>
<li>Conciliazioni stragiudiziali</li>
<li>Accordi transattivi</li>
</ul>"""
            }
        }
        
        created_count = 0
        for area in ServiceArea.objects.all():
            if area.slug in contenuti:
                # Verifica se la pagina esiste già
                if ServicePage.objects.filter(service_area=area).exists():
                    continue
                
                contenuto = contenuti[area.slug]
                page = ServicePage(
                    title=area.name,
                    slug=area.slug,
                    service_area=area,
                    subtitle=contenuto['subtitle'],
                    body=contenuto['body']
                )
                services_index.add_child(instance=page)
                created_count += 1
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✓ {created_count} pagine servizio create'))
        else:
            self.stdout.write('  - Pagine servizio già esistenti, saltate')

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
            settings.province = "Lazio"
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

    def _setup_demo_articles(self):
        """Crea articoli demo con contenuti realistici."""
        from home.models import HomePage
        from services.models import ServiceArea
        from articles.models import ArticleCategory, ArticleIndexPage, ArticlePage
        
        home = HomePage.objects.first()
        if not home:
            return
        
        # Crea categorie
        categories = {
            'guide': ArticleCategory.objects.get_or_create(
                slug='guide-legali',
                defaults={'name': 'Guide Legali', 'order': 1}
            )[0],
            'news': ArticleCategory.objects.get_or_create(
                slug='novita-normative',
                defaults={'name': 'Novità Normative', 'order': 2}
            )[0],
            'sentenze': ArticleCategory.objects.get_or_create(
                slug='sentenze-commenti',
                defaults={'name': 'Sentenze e Commenti', 'order': 3}
            )[0],
        }
        self.stdout.write(self.style.SUCCESS('  ✓ Categorie articoli create'))
        
        # Crea pagina indice articoli
        if not ArticleIndexPage.objects.exists():
            article_index = ArticleIndexPage(
                title='Articoli e Approfondimenti',
                slug='articoli',
                intro='Approfondimenti legali, guide pratiche e aggiornamenti normativi a cura dello Studio.'
            )
            home.add_child(instance=article_index)
            self.stdout.write(self.style.SUCCESS('  ✓ Pagina indice articoli creata'))
        else:
            article_index = ArticleIndexPage.objects.first()
            self.stdout.write('  - Pagina indice articoli già esistente, saltata')
        
        # Mappa aree di attività
        areas = {area.slug: area for area in ServiceArea.objects.all()}
        
        # Articoli demo con contenuti realistici
        articoli = [
            {
                'title': 'Guida in stato di ebbrezza: cosa fare se si viene fermati',
                'slug': 'guida-stato-ebbrezza-cosa-fare',
                'category': categories['guide'],
                'service_areas': ['diritto-penale'],
                'subtitle': 'Le procedure, i diritti dell\'automobilista e le conseguenze penali e amministrative',
                'body': """<p>Essere fermati alla guida con un tasso alcolemico superiore ai limiti di legge è un'esperienza che può avere conseguenze significative. Ecco cosa sapere per tutelare i propri diritti.</p>

<h3>I limiti di legge</h3>
<p>Il Codice della Strada prevede tre fasce di rilevanza:</p>
<ul>
<li><strong>Da 0,5 a 0,8 g/l</strong>: illecito amministrativo con sanzione pecuniaria e sospensione patente da 3 a 6 mesi</li>
<li><strong>Da 0,8 a 1,5 g/l</strong>: reato contravvenzionale con ammenda, arresto fino a 6 mesi e sospensione patente da 6 mesi a 1 anno</li>
<li><strong>Oltre 1,5 g/l</strong>: reato con ammenda, arresto fino a 1 anno e sospensione patente da 1 a 2 anni</li>
</ul>

<h3>I diritti al momento del controllo</h3>
<p>Chi viene sottoposto ad accertamento ha diritto a:</p>
<ul>
<li>Essere informato delle modalità di svolgimento del test</li>
<li>Richiedere un secondo prelievo ematico presso una struttura sanitaria</li>
<li>Farsi assistere da un legale durante le operazioni</li>
</ul>

<h3>Le conseguenze sul lavoro</h3>
<p>Una condanna per guida in stato di ebbrezza può avere ripercussioni anche in ambito lavorativo, specialmente per chi necessita della patente per svolgere la propria attività professionale. È importante valutare fin da subito strategie difensive che possano limitare gli effetti collaterali.</p>

<h3>Cosa fare</h3>
<p>Il consiglio è di rivolgersi tempestivamente a un avvocato penalista per valutare la regolarità delle procedure di accertamento e individuare la strategia difensiva più adeguata al caso specifico.</p>"""
            },
            {
                'title': 'Separazione consensuale: tempi, costi e procedura',
                'slug': 'separazione-consensuale-guida-completa',
                'category': categories['guide'],
                'service_areas': ['famiglia-successioni'],
                'subtitle': 'Come funziona la separazione consensuale, quanto costa e quali sono i tempi medi',
                'body': """<p>Quando una coppia decide di interrompere la convivenza di comune accordo, la separazione consensuale rappresenta la soluzione più rapida ed economica. Vediamo come funziona.</p>

<h3>Cos'è la separazione consensuale</h3>
<p>A differenza della separazione giudiziale, quella consensuale presuppone l'accordo dei coniugi su tutti gli aspetti: assegnazione della casa coniugale, affidamento dei figli, mantenimento, divisione dei beni.</p>

<h3>Le tre modalità</h3>
<p>Oggi esistono tre strade per separarsi consensualmente:</p>
<ul>
<li><strong>In Tribunale</strong>: i coniugi compaiono davanti al giudice che verifica l'accordo e lo omologa</li>
<li><strong>Negoziazione assistita</strong>: ciascun coniuge con il proprio avvocato sottoscrive un accordo che viene trasmesso al Procuratore della Repubblica</li>
<li><strong>In Comune</strong>: solo per coppie senza figli minori e senza trasferimenti immobiliari, davanti all'Ufficiale di Stato Civile</li>
</ul>

<h3>Tempi e costi</h3>
<p>La procedura in Tribunale richiede mediamente 2-3 mesi dall'iscrizione a ruolo all'udienza presidenziale. La negoziazione assistita può concludersi anche in poche settimane. I costi dipendono dalla complessità della situazione patrimoniale e dalla necessità di regolamentare l'affidamento dei figli.</p>

<h3>Dopo la separazione</h3>
<p>Trascorsi sei mesi dalla separazione consensuale (12 mesi da quella giudiziale), è possibile richiedere il divorzio. Anche il divorzio può essere consensuale o giudiziale.</p>"""
            },
            {
                'title': 'Ritardo nella consegna dell\'auto nuova: come farsi risarcire',
                'slug': 'ritardo-consegna-auto-risarcimento',
                'category': categories['news'],
                'service_areas': ['consumatori', 'diritto-civile'],
                'subtitle': 'Cosa fare quando il concessionario non rispetta i tempi di consegna pattuiti',
                'body': """<p>Negli ultimi anni, la crisi dei semiconduttori e le difficoltà nelle catene di approvvigionamento hanno causato ritardi significativi nella consegna di auto nuove. Ma quali sono i diritti del consumatore?</p>

<h3>Il contratto fa legge tra le parti</h3>
<p>Quando si ordina un'auto nuova, il contratto dovrebbe indicare una data di consegna, anche approssimativa. Se questa data viene superata senza giustificazioni, il consumatore ha diritto a:</p>
<ul>
<li>Sollecitare la consegna con diffida formale</li>
<li>Recedere dal contratto senza penali</li>
<li>Richiedere il risarcimento dei danni</li>
</ul>

<h3>La messa in mora</h3>
<p>Il primo passo è inviare una diffida scritta (raccomandata o PEC) al concessionario, fissando un termine ultimo per la consegna. È importante conservare tutta la documentazione: contratto, preventivi, email, messaggi.</p>

<h3>Quali danni si possono richiedere</h3>
<p>Il consumatore può chiedere il rimborso di:</p>
<ul>
<li>Spese di noleggio auto sostenute nell'attesa</li>
<li>Maggior costo dell'assicurazione per l'auto vecchia</li>
<li>Perdita di incentivi statali scaduti nel frattempo</li>
<li>Eventuali danni da fermo attività per veicoli commerciali</li>
</ul>

<h3>La conciliazione</h3>
<p>Prima di intraprendere azioni legali, può essere utile tentare una conciliazione presso le Camere di Commercio o attraverso le associazioni consumatori. Spesso il concessionario preferisce trovare un accordo piuttosto che affrontare un contenzioso.</p>"""
            },
            {
                'title': 'Licenziamento per giusta causa: quando è legittimo',
                'slug': 'licenziamento-giusta-causa-quando-legittimo',
                'category': categories['sentenze'],
                'service_areas': ['diritto-lavoro'],
                'subtitle': 'Analisi dei casi in cui il datore di lavoro può recedere immediatamente dal rapporto',
                'body': """<p>Il licenziamento per giusta causa è la forma più grave di recesso dal rapporto di lavoro: non prevede preavviso e comporta conseguenze immediate per il lavoratore. Ma quando è legittimo?</p>

<h3>La definizione normativa</h3>
<p>L'art. 2119 del Codice Civile prevede che ciascuna delle parti possa recedere dal contratto "qualora si verifichi una causa che non consenta la prosecuzione, anche provvisoria, del rapporto". La giurisprudenza ha elaborato nel tempo criteri precisi.</p>

<h3>Casi tipici riconosciuti dalla giurisprudenza</h3>
<ul>
<li>Furto o sottrazione di beni aziendali, anche di modico valore</li>
<li>Violazione dell'obbligo di fedeltà (es. concorrenza sleale)</li>
<li>Insubordinazione grave verso i superiori</li>
<li>Falsa malattia o abuso dei permessi</li>
<li>Violazione delle norme di sicurezza con messa in pericolo di terzi</li>
</ul>

<h3>Il principio di proporzionalità</h3>
<p>La Cassazione ha più volte ribadito che il licenziamento deve essere proporzionato alla gravità del fatto contestato. Un singolo ritardo, ad esempio, non giustifica il recesso immediato se non inserito in un contesto di recidiva documentata.</p>

<h3>Come impugnare</h3>
<p>Il lavoratore ha 60 giorni dalla comunicazione del licenziamento per impugnarlo stragiudizialmente (raccomandata o PEC) e successivamente 180 giorni per depositare ricorso in Tribunale. La tempestività è fondamentale per non perdere il diritto alla tutela.</p>"""
            },
            {
                'title': 'Ricorso al TAR: quando conviene e quanto costa',
                'slug': 'ricorso-tar-quando-conviene-costi',
                'category': categories['guide'],
                'service_areas': ['diritto-amministrativo'],
                'subtitle': 'Guida pratica al ricorso contro provvedimenti della Pubblica Amministrazione',
                'body': """<p>Hai ricevuto un provvedimento sfavorevole da un ente pubblico? Forse il TAR può annullarlo. Ecco cosa sapere prima di decidere.</p>

<h3>Cosa si può impugnare</h3>
<p>Al Tribunale Amministrativo Regionale si possono impugnare:</p>
<ul>
<li>Provvedimenti di diniego (permessi, autorizzazioni, concessioni)</li>
<li>Ordinanze comunali (demolizione, sgombero, chiusura attività)</li>
<li>Esclusioni da concorsi e gare d'appalto</li>
<li>Sanzioni amministrative non devolute al giudice ordinario</li>
<li>Atti in materia urbanistica ed edilizia</li>
</ul>

<h3>I termini perentori</h3>
<p>Attenzione: il ricorso va notificato entro <strong>60 giorni</strong> dalla notifica o dalla piena conoscenza del provvedimento. Per gli appalti pubblici il termine è di soli <strong>30 giorni</strong>. Il ritardo anche di un solo giorno comporta l'inammissibilità.</p>

<h3>I costi</h3>
<p>Il contributo unificato varia da 300 a 4.000 euro a seconda della materia e del valore della controversia. A questo si aggiungono i diritti di segreteria, le spese di notifica e l'onorario dell'avvocato. In caso di soccombenza, si rischia la condanna alle spese della controparte.</p>

<h3>Le misure cautelari</h3>
<p>Se il provvedimento produce effetti immediati e irreversibili (es. demolizione imminente), si può chiedere la sospensione cautelare. Il giudice può concederla con decreto monocratico in casi urgentissimi, anche prima della discussione collegiale.</p>"""
            },
            {
                'title': 'Decreto ingiuntivo non pagato: cosa succede dopo',
                'slug': 'decreto-ingiuntivo-non-pagato-conseguenze',
                'category': categories['guide'],
                'service_areas': ['recupero-crediti', 'diritto-civile'],
                'subtitle': 'Le fasi successive all\'ottenimento del decreto e i tempi del recupero forzoso',
                'body': """<p>Hai ottenuto un decreto ingiuntivo ma il debitore non paga? Ecco cosa puoi fare per recuperare il tuo credito.</p>

<h3>La formula esecutiva</h3>
<p>Trascorsi 40 giorni dalla notifica senza opposizione, il decreto diventa definitivo. Si richiede quindi alla cancelleria l'apposizione della formula esecutiva, che lo rende titolo idoneo per l'esecuzione forzata.</p>

<h3>L'atto di precetto</h3>
<p>Prima del pignoramento, è obbligatorio notificare l'atto di precetto: un'intimazione formale al debitore a pagare entro 10 giorni. È l'ultima occasione per un pagamento spontaneo.</p>

<h3>Le forme di pignoramento</h3>
<ul>
<li><strong>Pignoramento mobiliare</strong>: l'ufficiale giudiziario si reca presso il debitore per inventariare beni vendibili</li>
<li><strong>Pignoramento immobiliare</strong>: si trascrive il pignoramento su immobili di proprietà del debitore</li>
<li><strong>Pignoramento presso terzi</strong>: si "blocca" lo stipendio, la pensione o il conto corrente del debitore</li>
</ul>

<h3>Quanto si può pignorare dello stipendio</h3>
<p>Per crediti ordinari: massimo un quinto dello stipendio netto. La pensione è pignorabile solo per la parte eccedente il minimo vitale (attualmente circa 1.000 euro). Il conto corrente può essere bloccato integralmente, salvo somme impignorabili per legge.</p>

<h3>Tempi realistici</h3>
<p>Dal decreto ingiuntivo all'effettivo recupero possono passare da pochi mesi (pignoramento presso terzi) a diversi anni (vendita immobiliare). Una valutazione preventiva della solvibilità del debitore è fondamentale.</p>"""
            },
            {
                'title': 'Mediazione obbligatoria: come prepararsi all\'incontro',
                'slug': 'mediazione-obbligatoria-come-prepararsi',
                'category': categories['guide'],
                'service_areas': ['mediazione-negoziazione'],
                'subtitle': 'Consigli pratici per affrontare la mediazione civile con le migliori probabilità di successo',
                'body': """<p>In molte materie civili, prima di poter andare in Tribunale è obbligatorio tentare la mediazione. Ecco come sfruttare al meglio questa opportunità.</p>

<h3>Quando è obbligatoria</h3>
<p>La mediazione è condizione di procedibilità per controversie in materia di:</p>
<ul>
<li>Condominio e diritti reali</li>
<li>Divisione ereditaria</li>
<li>Locazioni e comodato</li>
<li>Risarcimento danni da responsabilità medica</li>
<li>Contratti assicurativi, bancari e finanziari</li>
</ul>

<h3>Prima dell'incontro</h3>
<p>È fondamentale arrivare preparati:</p>
<ul>
<li>Raccogliere tutta la documentazione a supporto delle proprie ragioni</li>
<li>Definire con l'avvocato gli obiettivi minimi e massimi accettabili</li>
<li>Valutare realisticamente i costi e i tempi di un eventuale giudizio</li>
<li>Essere disposti ad ascoltare le ragioni dell'altra parte</li>
</ul>

<h3>Durante la mediazione</h3>
<p>Il mediatore non decide chi ha ragione, ma facilita il dialogo tra le parti. Le dichiarazioni rese in mediazione sono riservate e non possono essere usate in un successivo giudizio. Questo favorisce un confronto più aperto.</p>

<h3>Se si raggiunge l'accordo</h3>
<p>Il verbale di accordo, sottoscritto dalle parti e dagli avvocati, costituisce titolo esecutivo. Significa che se una parte non adempie, l'altra può procedere direttamente al pignoramento senza passare per un giudizio di cognizione.</p>

<h3>Se non si raggiunge l'accordo</h3>
<p>La condizione di procedibilità è comunque soddisfatta. Si potrà depositare ricorso in Tribunale allegando il verbale di mancato accordo. Il giudice terrà conto del comportamento delle parti in mediazione ai fini delle spese processuali.</p>"""
            },
            {
                'title': 'Eredità con debiti: come tutelarsi',
                'slug': 'eredita-con-debiti-come-tutelarsi',
                'category': categories['news'],
                'service_areas': ['famiglia-successioni'],
                'subtitle': 'Accettazione con beneficio d\'inventario e rinuncia: quando e come esercitarle',
                'body': """<p>Ereditare non è sempre una fortuna. Quando il defunto lascia debiti superiori all'attivo, accettare l'eredità può trasformarsi in un problema. Ecco come evitarlo.</p>

<h3>Tre opzioni</h3>
<p>Chiamato all'eredità, hai tre possibilità:</p>
<ul>
<li><strong>Accettazione pura e semplice</strong>: diventi erede e rispondi dei debiti anche con il tuo patrimonio personale</li>
<li><strong>Accettazione con beneficio d'inventario</strong>: rispondi dei debiti solo nei limiti di quanto ereditato</li>
<li><strong>Rinuncia</strong>: non diventi erede e non rispondi di nulla</li>
</ul>

<h3>Il beneficio d'inventario</h3>
<p>È la soluzione ideale quando non si conosce l'esatta situazione patrimoniale del defunto. Si presenta dichiarazione in Tribunale e si procede alla redazione dell'inventario dei beni. I creditori potranno soddisfarsi solo su questi.</p>

<h3>Attenzione ai comportamenti concludenti</h3>
<p>Chi compie atti che presuppongono la volontà di accettare (es. vendere un bene ereditario, riscuotere crediti del defunto) perde il diritto di rinunciare o di accettare con beneficio. Questo vale anche per atti apparentemente banali.</p>

<h3>Termini</h3>
<p>Hai 10 anni per accettare l'eredità. Ma attenzione: i creditori possono fissare un termine più breve con apposita istanza al giudice. La rinuncia va fatta con dichiarazione in Tribunale o davanti a un notaio.</p>

<h3>Minorenni e incapaci</h3>
<p>Per i minorenni e gli incapaci, l'accettazione avviene sempre con beneficio d'inventario. È una forma di tutela automatica prevista dalla legge che impedisce di pregiudicare il loro patrimonio.</p>"""
            },
        ]
        
        from django.utils import timezone
        from datetime import timedelta
        
        created_count = 0
        base_date = timezone.now() - timedelta(days=len(articoli))  # Date scaglionate
        
        for i, art in enumerate(articoli):
            if ArticlePage.objects.filter(slug=art['slug']).exists():
                continue
            
            article = ArticlePage(
                title=art['title'],
                slug=art['slug'],
                category=art['category'],
                subtitle=art['subtitle'],
                body=art['body']
            )
            article_index.add_child(instance=article)
            
            # Imposta la data di pubblicazione (scaglionata)
            pub_date = base_date + timedelta(days=i)
            article.first_published_at = pub_date
            article.last_published_at = pub_date
            
            # Collega aree di attività
            for area_slug in art['service_areas']:
                if area_slug in areas:
                    article.service_areas.add(areas[area_slug])
            article.save()
            created_count += 1
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✓ {created_count} articoli demo creati'))
        else:
            self.stdout.write('  - Articoli demo già esistenti, saltati')

