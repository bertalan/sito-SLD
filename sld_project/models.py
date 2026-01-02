"""
Site-wide settings editable from Wagtail admin.
"""
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.documents import get_document_model_string


@register_setting(icon="cog")
class SiteSettings(BaseSiteSetting):
    """Impostazioni globali dello studio legale, editabili dall'admin."""
    
    class Meta:
        verbose_name = "Impostazioni Studio"
        verbose_name_plural = "Impostazioni Studio"
    
    # Info Studio
    studio_name = models.CharField(
        "Nome Studio", 
        max_length=200, 
        default="Studio Legale",
        help_text="Es: Studio Legale Rossi"
    )
    logo = models.ForeignKey(
        get_document_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Logo",
        help_text="Logo dello studio (SVG, PNG o JPG)"
    )
    lawyer_name = models.CharField(
        "Nome Avvocato", 
        max_length=200, 
        default="Avv. Mario Rossi",
        help_text="Nome completo con titolo"
    )
    
    # Contatti
    email = models.EmailField(
        "Email", 
        default="info@example.com"
    )
    email_pec = models.EmailField(
        "PEC", 
        default="avvocato@pec.it"
    )
    phone = models.CharField(
        "Telefono", 
        max_length=30, 
        default="+39 06 12345678"
    )
    mobile_phone = models.CharField(
        "Cellulare", 
        max_length=30, 
        blank=True,
        help_text="Opzionale - visibile solo se compilato"
    )
    
    # Sede
    address = models.CharField(
        "Indirizzo", 
        max_length=300, 
        default="Via Roma, 1 - 00100 Roma"
    )
    city = models.CharField(
        "Città", 
        max_length=100, 
        default="Roma"
    )
    maps_url = models.URLField(
        "URL Mappa", 
        default="https://maps.apple.com/?daddr=41.9028,12.4964",
        help_text="Link Apple Maps o Google Maps"
    )
    maps_lat = models.DecimalField(
        "Latitudine", 
        max_digits=10, 
        decimal_places=6, 
        default=41.902782
    )
    maps_lng = models.DecimalField(
        "Longitudine", 
        max_digits=10, 
        decimal_places=6, 
        default=12.496366
    )
    
    # Web & Social
    website = models.CharField(
        "Sito Web", 
        max_length=200, 
        default="www.example.com"
    )
    facebook_url = models.URLField(
        "Facebook", 
        blank=True,
        help_text="URL completo della pagina Facebook"
    )
    twitter_handle = models.CharField(
        "Twitter/X", 
        max_length=50, 
        blank=True,
        help_text="Es: @avvocato"
    )
    linkedin_url = models.URLField(
        "LinkedIn", 
        blank=True
    )
    
    # Jitsi
    jitsi_room_prefix = models.CharField(
        "Prefisso stanza Jitsi",
        max_length=50,
        default="StudioLegale",
        help_text="Prefisso per le stanze videochiamata (senza spazi)"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DOMICILIAZIONI
    # ═══════════════════════════════════════════════════════════════════════════
    
    domiciliazioni_tribunali = models.TextField(
        "Tribunali / Uffici",
        blank=True,
        default="roma|Tribunale di Roma\ncorte_appello|Corte d'Appello di Roma\ngdp|Giudice di Pace di Roma\ntar|TAR Lazio\nunep|Ufficio UNEP di Roma",
        help_text="Una voce per riga. Formato: codice|Etichetta visibile. Es: roma|Tribunale di Roma"
    )
    domiciliazioni_tipi_udienza = models.TextField(
        "Tipi Udienza / Servizio",
        blank=True,
        default="civile|Udienza Civile\npenale|Udienza Penale\nlavoro|Udienza Lavoro\nfamiglia|Udienza Famiglia\nesecuzioni|Esecuzioni\nfallimentare|Fallimentare\nvolontaria|Volontaria Giurisdizione\nnotificazioni|Ufficio notificazioni\nesecuzione_protesti|Ufficio esecuzione e protesti\naltro|Altro",
        help_text="Una voce per riga. Formato: codice|Etichetta visibile. Es: civile|Udienza Civile"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAGAMENTI
    # ═══════════════════════════════════════════════════════════════════════════
    
    PAYMENT_MODE_CHOICES = [
        ('demo', 'Demo (simulato)'),
        ('sandbox', 'Sandbox (test)'),
        ('live', 'Live (produzione)'),
    ]
    
    payment_mode = models.CharField(
        "Modalità pagamento",
        max_length=10,
        choices=PAYMENT_MODE_CHOICES,
        default="demo",
        help_text="ℹ️ Demo: simula pagamenti (per sviluppo). Sandbox: usa chiavi di test Stripe/PayPal. Live: pagamenti reali."
    )
    
    # Stripe
    stripe_public_key = models.CharField(
        "Stripe Public Key",
        max_length=200,
        blank=True,
        help_text="ℹ️ Trova in: Stripe Dashboard → Developers → API Keys → Publishable key (pk_test_... o pk_live_...)"
    )
    stripe_secret_key = models.CharField(
        "Stripe Secret Key",
        max_length=200,
        blank=True,
        help_text="ℹ️ Trova in: Stripe Dashboard → Developers → API Keys → Secret key (sk_test_... o sk_live_...). MAI condividere!"
    )
    stripe_webhook_secret = models.CharField(
        "Stripe Webhook Secret",
        max_length=200,
        blank=True,
        help_text="ℹ️ Trova in: Stripe Dashboard → Developers → Webhooks → Signing secret (whsec_...). Serve per confermare pagamenti."
    )
    
    # PayPal
    paypal_client_id = models.CharField(
        "PayPal Client ID",
        max_length=200,
        blank=True,
        help_text="ℹ️ Trova in: PayPal Developer → My Apps & Credentials → App → Client ID"
    )
    paypal_client_secret = models.CharField(
        "PayPal Client Secret",
        max_length=200,
        blank=True,
        help_text="ℹ️ Trova in: PayPal Developer → My Apps & Credentials → App → Secret. MAI condividere!"
    )
    
    # Booking
    booking_slot_duration = models.PositiveIntegerField(
        "Durata slot (minuti)",
        default=30,
        help_text="Durata di ogni slot prenotabile in minuti"
    )
    booking_price_cents = models.PositiveIntegerField(
        "Prezzo consulenza (centesimi)",
        default=6000,
        help_text="ℹ️ Prezzo in centesimi: 6000 = €60,00"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EMAIL SMTP
    # ═══════════════════════════════════════════════════════════════════════════
    
    email_host = models.CharField(
        "Server SMTP",
        max_length=200,
        blank=True,
        help_text="ℹ️ Esempio: smtp.gmail.com, smtp.office365.com, smtp.tuoserver.it"
    )
    email_port = models.PositiveIntegerField(
        "Porta SMTP",
        default=587,
        help_text="ℹ️ Porte comuni: 587 (TLS), 465 (SSL), 25 (non criptata)"
    )
    email_use_tls = models.BooleanField(
        "Usa TLS",
        default=True,
        help_text="Attiva per connessione sicura (raccomandato)"
    )
    email_host_user = models.CharField(
        "Username SMTP",
        max_length=200,
        blank=True,
        help_text="ℹ️ Solitamente l'indirizzo email completo"
    )
    email_host_password = models.CharField(
        "Password SMTP",
        max_length=200,
        blank=True,
        help_text="ℹ️ Per Gmail con 2FA: usa 'Password per le app' da Sicurezza account"
    )
    email_from_address = models.CharField(
        "Email mittente",
        max_length=200,
        blank=True,
        help_text="ℹ️ Formato: 'Studio Legale <info@example.com>'"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════════
    
    ga4_measurement_id = models.CharField(
        "Google Analytics 4 ID",
        max_length=50,
        blank=True,
        help_text="ℹ️ Trova in: Google Analytics → Admin → Data Streams → Measurement ID (G-XXXXXXXXXX)"
    )
    matomo_url = models.URLField(
        "Matomo URL",
        blank=True,
        help_text="ℹ️ URL della tua installazione Matomo (es: https://matomo.example.com)"
    )
    matomo_site_id = models.CharField(
        "Matomo Site ID",
        max_length=10,
        blank=True,
        help_text="ℹ️ Trova in: Matomo → Impostazioni → Siti Web → ID del sito"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GOOGLE CALENDAR
    # ═══════════════════════════════════════════════════════════════════════════
    
    google_calendar_ical_url = models.URLField(
        "Google Calendar iCal URL",
        blank=True,
        help_text="ℹ️ Trova in: Google Calendar → Impostazioni → Integra calendario → Indirizzo segreto in formato iCal"
    )
    google_calendar_cache_ttl = models.PositiveIntegerField(
        "Cache Google Calendar (secondi)",
        default=600,
        help_text="Durata cache eventi calendario. Default: 600 = 10 minuti"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAGINE LEGALI
    # ═══════════════════════════════════════════════════════════════════════════
    
    privacy_policy = models.TextField(
        "Privacy Policy",
        blank=True,
        help_text="Testo completo della Privacy Policy. Usa HTML per la formattazione. Le variabili {{studio_name}}, {{lawyer_name}}, {{address}}, {{city}}, {{email}}, {{email_pec}}, {{phone}} verranno sostituite automaticamente."
    )
    terms_conditions = models.TextField(
        "Termini e Condizioni",
        blank=True,
        help_text="Testo completo dei Termini e Condizioni. Usa HTML per la formattazione. Le variabili {{studio_name}}, {{lawyer_name}}, {{address}}, {{city}}, {{email}}, {{email_pec}}, {{phone}} verranno sostituite automaticamente."
    )
    
    panels = [
        MultiFieldPanel([
            FieldPanel('studio_name'),
            FieldPanel('logo'),
            FieldPanel('lawyer_name'),
        ], heading="Identità Studio"),
        MultiFieldPanel([
            FieldPanel('email'),
            FieldPanel('email_pec'),
            FieldPanel('phone'),
            FieldPanel('mobile_phone'),
        ], heading="Contatti"),
        MultiFieldPanel([
            FieldPanel('address'),
            FieldPanel('city'),
            FieldPanel('maps_url'),
            FieldPanel('maps_lat'),
            FieldPanel('maps_lng'),
        ], heading="Sede"),
        MultiFieldPanel([
            FieldPanel('website'),
            FieldPanel('facebook_url'),
            FieldPanel('twitter_handle'),
            FieldPanel('linkedin_url'),
        ], heading="Web & Social"),
        MultiFieldPanel([
            FieldPanel('jitsi_room_prefix'),
        ], heading="Videochiamate"),
        MultiFieldPanel([
            FieldPanel('domiciliazioni_tribunali'),
            FieldPanel('domiciliazioni_tipi_udienza'),
        ], heading="📋 Domiciliazioni", classname="collapsible"),
        MultiFieldPanel([
            FieldPanel('payment_mode'),
            FieldPanel('booking_slot_duration'),
            FieldPanel('booking_price_cents'),
        ], heading="💳 Prenotazioni", classname="collapsible"),
        MultiFieldPanel([
            FieldPanel('stripe_public_key'),
            FieldPanel('stripe_secret_key'),
            FieldPanel('stripe_webhook_secret'),
        ], heading="💳 Stripe", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('paypal_client_id'),
            FieldPanel('paypal_client_secret'),
        ], heading="💳 PayPal", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('email_host'),
            FieldPanel('email_port'),
            FieldPanel('email_use_tls'),
            FieldPanel('email_host_user'),
            FieldPanel('email_host_password'),
            FieldPanel('email_from_address'),
        ], heading="📧 Email SMTP", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('ga4_measurement_id'),
            FieldPanel('matomo_url'),
            FieldPanel('matomo_site_id'),
        ], heading="📊 Analytics", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('google_calendar_ical_url'),
            FieldPanel('google_calendar_cache_ttl'),
        ], heading="📅 Google Calendar", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('privacy_policy'),
            FieldPanel('terms_conditions'),
        ], heading="📄 Pagine Legali", classname="collapsible collapsed"),
    ]
    
    @classmethod
    def get_current(cls):
        """
        Helper per ottenere le impostazioni del sito corrente.
        Usare questo metodo nel codice Python (views, email_service, ecc.)
        """
        from wagtail.models import Site
        try:
            site = Site.objects.filter(is_default_site=True).first()
            if site:
                return cls.for_site(site)
        except Exception:
            pass
        # Ritorna un'istanza vuota con i default
        return cls()
    
    def get_contact_dict(self):
        """Ritorna un dizionario con tutti i dati di contatto."""
        return {
            'studio_name': self.studio_name,
            'lawyer_name': self.lawyer_name,
            'email': self.email,
            'email_pec': self.email_pec,
            'phone': self.phone,
            'mobile_phone': self.mobile_phone,
            'address': self.address,
            'city': self.city,
            'maps_url': self.maps_url,
            'website': self.website,
        }

    def _parse_choices(self, text):
        """Parsa un campo testo in lista di tuple (codice, etichetta)."""
        choices = []
        if not text:
            return choices
        for line in text.strip().split('\n'):
            line = line.strip()
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    choices.append((parts[0].strip(), parts[1].strip()))
        return choices

    def get_tribunali_choices(self):
        """Ritorna le choices per tribunali come lista di tuple."""
        return self._parse_choices(self.domiciliazioni_tribunali)
    
    def get_tipi_udienza_choices(self):
        """Ritorna le choices per tipi udienza come lista di tuple."""
        return self._parse_choices(self.domiciliazioni_tipi_udienza)
