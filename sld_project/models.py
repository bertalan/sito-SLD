"""
Site-wide settings editable from Wagtail admin.
"""
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


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
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Logo",
        help_text="Logo dello studio (SVG, PNG o JPG). Carica come immagine."
    )
    favicon = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Favicon",
        help_text="Icona del sito (PNG 32x32 o SVG). Carica come immagine."
    )
    default_social_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Immagine Social Default",
        help_text="Immagine 1200x630 px per condivisioni social (Facebook, Twitter, LinkedIn). Usata come fallback se la pagina non ha immagine."
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
        default="",
        blank=True,
        help_text="Email principale visibile ai clienti (es: info@studiolegalrossi.it)"
    )
    email_pec = models.EmailField(
        "PEC", 
        default="",
        blank=True,
        help_text="PEC per comunicazioni ufficiali (es: avvocato.rossi@pec.ordineavvocati.it)"
    )
    phone = models.CharField(
        "Telefono", 
        max_length=30, 
        default="",
        blank=True,
        help_text="Formato internazionale: +39 06 1234567"
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
        default="",
        blank=True,
        help_text="Indirizzo completo con CAP (es: Via Roma, 1 - 00100 Roma)"
    )
    city = models.CharField(
        "Città", 
        max_length=100, 
        default="",
        blank=True,
        help_text="Solo il nome della città (es: Roma, Milano, Bari)"
    )
    province = models.CharField(
        "Provincia/Regione",
        max_length=100,
        default="Lazio",
        help_text="Provincia o regione per SEO (es: Puglia, Lazio, Lombardia)"
    )
    maps_url = models.URLField(
        "URL Mappa", 
        default="",
        blank=True,
        help_text="Copia il link 'Condividi' da Google Maps o Apple Maps"
    )
    maps_lat = models.CharField(
        "Latitudine", 
        max_length=20,
        default="",
        blank=True,
        help_text="Clicca destro su Google Maps → 'Cosa c'è qui?' per vedere le coordinate (es: 41.902782)"
    )
    maps_lng = models.CharField(
        "Longitudine", 
        max_length=20,
        default="",
        blank=True,
        help_text="Seconda coordinata dopo la virgola (es: 12.496366)"
    )
    
    # Web & Social
    website = models.CharField(
        "Sito Web", 
        max_length=200, 
        default="",
        blank=True,
        help_text="Senza https:// (es: www.studiolegalrossi.it)"
    )
    facebook_url = models.URLField(
        "Facebook", 
        blank=True,
        help_text="URL completo (es: https://facebook.com/studiolegalrossi)"
    )
    x_url = models.URLField(
        "X (ex Twitter)", 
        blank=True,
        help_text="URL completo (es: https://x.com/avvrossi)"
    )
    linkedin_url = models.URLField(
        "LinkedIn", 
        blank=True,
        help_text="URL completo (es: https://linkedin.com/in/mariorossi)"
    )
    
    # Jitsi
    jitsi_room_prefix = models.CharField(
        "Prefisso stanza Jitsi",
        max_length=50,
        default="StudioLegale",
        help_text="Solo lettere senza spazi. Il link finale sarà: meet.jit.si/Prefisso-[codice casuale a 16 caratteri]"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COLORI BRAND
    # ═══════════════════════════════════════════════════════════════════════════
    
    color_black = models.CharField(
        "Colore Nero",
        max_length=7,
        default="#0a0a0a",
        help_text="Colore nero principale per testi e sfondi scuri (formato HEX: #000000)"
    )
    color_dark = models.CharField(
        "Colore Scuro",
        max_length=7,
        default="#1a1a1a",
        help_text="Grigio scuro per elementi secondari (formato HEX: #000000)"
    )
    color_gray = models.CharField(
        "Colore Grigio",
        max_length=7,
        default="#6b7280",
        help_text="Grigio per testi secondari (formato HEX: #000000)"
    )
    color_silver = models.CharField(
        "Colore Argento",
        max_length=7,
        default="#f5f5f5",
        help_text="Sfondo chiaro per sezioni alternate (formato HEX: #000000)"
    )
    color_white = models.CharField(
        "Colore Bianco",
        max_length=7,
        default="#ffffff",
        help_text="Bianco per sfondi e testi chiari (formato HEX: #000000)"
    )
    color_accent = models.CharField(
        "Colore Accento",
        max_length=7,
        default="#e91e63",
        help_text="Colore principale del brand per CTA, link e decorazioni (formato HEX: #000000)"
    )
    color_accent_hover = models.CharField(
        "Colore Accento Hover",
        max_length=7,
        default="#be185d",
        help_text="Colore accento al passaggio del mouse, tipicamente più scuro (formato HEX: #000000)"
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
    # NOTA: Tutte le configurazioni pagamento sono in .env per sicurezza:
    # - PAYMENT_MODE (demo/sandbox/live)
    # - STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
    # - PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_MODE
    
    # Booking
    booking_slot_duration = models.PositiveIntegerField(
        "Durata slot (minuti)",
        default=30,
        help_text="Valori consigliati: 15, 30, 45 o 60 minuti"
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
    
    # NOTA: google_calendar_ical_url è stato spostato in .env per sicurezza
    # (contiene un token segreto). Vedi: GOOGLE_CALENDAR_ICAL_URL
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
            FieldPanel('favicon'),
            FieldPanel('default_social_image'),
            FieldPanel('lawyer_name'),
        ], heading="Identità Studio"),
        MultiFieldPanel([
            FieldPanel('color_black'),
            FieldPanel('color_dark'),
            FieldPanel('color_gray'),
            FieldPanel('color_silver'),
            FieldPanel('color_white'),
            FieldPanel('color_accent'),
            FieldPanel('color_accent_hover'),
        ], heading="🎨 Colori Brand", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('email'),
            FieldPanel('email_pec'),
            FieldPanel('phone'),
            FieldPanel('mobile_phone'),
        ], heading="Contatti"),
        MultiFieldPanel([
            FieldPanel('address'),
            FieldPanel('city'),
            FieldPanel('province'),
            FieldPanel('maps_url'),
            FieldPanel('maps_lat'),
            FieldPanel('maps_lng'),
        ], heading="Sede"),
        MultiFieldPanel([
            FieldPanel('website'),
            FieldPanel('facebook_url'),
            FieldPanel('x_url'),
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
            FieldPanel('booking_slot_duration'),
            FieldPanel('booking_price_cents'),
        ], heading="💳 Prenotazioni", classname="collapsible"),
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
            FieldPanel('google_calendar_cache_ttl'),
        ], heading="📅 Google Calendar", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('privacy_policy'),
            FieldPanel('terms_conditions'),
        ], heading="📄 Pagine Legali", classname="collapsible collapsed"),
    ]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PROPRIETÀ PER VERIFICARE STATO CONFIGURAZIONE SEGRETI (da .env)
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def stripe_secret_configured(self):
        """Ritorna True se STRIPE_SECRET_KEY è configurata in .env"""
        import os
        return bool(os.environ.get('STRIPE_SECRET_KEY', ''))
    
    @property
    def stripe_webhook_configured(self):
        """Ritorna True se STRIPE_WEBHOOK_SECRET è configurata in .env"""
        import os
        return bool(os.environ.get('STRIPE_WEBHOOK_SECRET', ''))
    
    @property
    def paypal_secret_configured(self):
        """Ritorna True se PAYPAL_CLIENT_SECRET è configurata in .env"""
        import os
        return bool(os.environ.get('PAYPAL_CLIENT_SECRET', ''))
    
    @property
    def google_calendar_configured(self):
        """Ritorna True se GOOGLE_CALENDAR_ICAL_URL è configurata in .env"""
        import os
        return bool(os.environ.get('GOOGLE_CALENDAR_ICAL_URL', ''))
    
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
    
    def save(self, *args, **kwargs):
        """Normalizza le coordinate prima del salvataggio."""
        # Converti virgola in punto per le coordinate
        if self.maps_lat:
            self.maps_lat = str(self.maps_lat).replace(',', '.').strip()
        if self.maps_lng:
            self.maps_lng = str(self.maps_lng).replace(',', '.').strip()
        super().save(*args, **kwargs)
    
    def get_maps_lat_float(self):
        """Ritorna la latitudine come float."""
        try:
            return float(str(self.maps_lat).replace(',', '.'))
        except (ValueError, TypeError):
            return 41.902782
    
    def get_maps_lng_float(self):
        """Ritorna la longitudine come float."""
        try:
            return float(str(self.maps_lng).replace(',', '.'))
        except (ValueError, TypeError):
            return 12.496366
    
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

    def get_brand_colors(self):
        """Ritorna un dizionario con i colori del brand."""
        return {
            'brand-black': self.color_black or '#0a0a0a',
            'brand-dark': self.color_dark or '#1a1a1a',
            'brand-gray': self.color_gray or '#6b7280',
            'brand-silver': self.color_silver or '#f5f5f5',
            'brand-white': self.color_white or '#ffffff',
            'brand-accent': self.color_accent or '#e91e63',
            'brand-accent-hover': self.color_accent_hover or '#be185d',
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
