from django.db import models
from django.utils.html import format_html
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.snippets.models import register_snippet


class DomiciliazioniFormField(AbstractFormField):
    """Campo form per domiciliazioni."""
    page = ParentalKey('DomiciliazioniPage', on_delete=models.CASCADE, related_name='form_fields')


class DomiciliazioniPage(AbstractEmailForm):
    """Pagina domiciliazioni con form e upload documenti."""
    
    intro = RichTextField("Introduzione", blank=True)
    service_description = RichTextField("Descrizione servizio", blank=True)
    thank_you_text = RichTextField("Testo ringraziamento", blank=True)
    tribunali = models.TextField("Tribunali coperti", blank=True, help_text="Uno per riga")
    
    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('intro'),
        FieldPanel('service_description'),
        FieldPanel('tribunali'),
        InlinePanel('form_fields', label="Campi del form"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldPanel('to_address'),
            FieldPanel('from_address'),
            FieldPanel('subject'),
        ], heading="Email"),
    ]
    
    class Meta:
        verbose_name = "Pagina Domiciliazioni"
    
    def get_tribunali_list(self):
        if self.tribunali:
            return [t.strip() for t in self.tribunali.split('\n') if t.strip()]
        return []
    
    def serve(self, request):
        from django.shortcuts import render, redirect
        from .views import process_domiciliazione_form
        
        if request.method == 'POST':
            submission = process_domiciliazione_form(request, self)
            if submission:
                # Mostra pagina di ringraziamento
                return render(request, 'domiciliazioni/domiciliazioni_landing.html', {
                    'page': self,
                    'submission': submission,
                })
        
        # GET: mostra il form
        return render(request, 'domiciliazioni/domiciliazioni_page.html', {
            'page': self,
            'self': self,
        })


# Scelte per tipo udienza/servizio
TIPO_UDIENZA_CHOICES = [
    ('civile', 'Udienza Civile'),
    ('penale', 'Udienza Penale'),
    ('lavoro', 'Udienza Lavoro'),
    ('famiglia', 'Udienza Famiglia'),
    ('esecuzioni', 'Esecuzioni'),
    ('fallimentare', 'Fallimentare'),
    ('volontaria', 'Volontaria Giurisdizione'),
    ('notificazioni', 'Ufficio notificazioni'),
    ('esecuzione_protesti', 'Ufficio esecuzione e protesti'),
    ('altro', 'Altro'),
]

# Scelte per tribunale/ufficio
TRIBUNALE_CHOICES = [
    ('lecce', 'Tribunale di Lecce'),
    ('unep', 'Ufficio UNEP di Lecce'),
]


class DomiciliazioniSubmission(ClusterableModel):
    """Submission domiciliazione con allegati."""
    
    STATUS_CHOICES = [
        ('pending', 'In attesa'),
        ('accepted', 'Accettata'),
        ('completed', 'Completata'),
        ('cancelled', 'Annullata'),
    ]
    
    page = models.ForeignKey(DomiciliazioniPage, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    form_data = models.JSONField(default=dict, blank=True)
    submit_time = models.DateTimeField(auto_now_add=True)
    
    # Dati avvocato richiedente
    nome_avvocato = models.CharField("Nome e Cognome Avvocato", max_length=200)
    email = models.EmailField("Email")
    telefono = models.CharField("Telefono", max_length=30, blank=True)
    ordine_appartenenza = models.CharField("Ordine di appartenenza", max_length=100, blank=True)
    
    # Dati udienza
    tribunale = models.CharField("Tribunale", max_length=100, choices=TRIBUNALE_CHOICES)
    sezione = models.CharField("Sezione", max_length=50, blank=True, help_text="Es: Sezione Civile, Sezione Lavoro")
    giudice = models.CharField("Giudice", max_length=100, blank=True)
    tipo_udienza = models.CharField("Tipo udienza", max_length=100, choices=TIPO_UDIENZA_CHOICES, default='civile')
    
    # Dati causa
    numero_rg = models.CharField("Numero R.G.", max_length=50, default='', help_text="Numero di Ruolo Generale (es: 1234/2025)")
    parti_causa = models.TextField("Parti in causa", blank=True, help_text="Attore vs Convenuto")
    
    # Data e ora udienza
    data_udienza = models.DateField("Data udienza", null=True, blank=True)
    ora_udienza = models.TimeField("Ora udienza", null=True, blank=True)
    
    # Attività richieste
    attivita_richieste = models.TextField("Attività richieste", blank=True, 
        help_text="Descrivi le attività da svolgere in udienza (es: mera comparizione, deposito atti, richiesta rinvio)")
    
    # Note e istruzioni
    note = models.TextField("Note e istruzioni", blank=True)
    
    # Stato
    status = models.CharField("Stato", max_length=20, choices=STATUS_CHOICES, default='pending')
    esito_udienza = models.TextField("Esito udienza", blank=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('nome_avvocato'),
            FieldPanel('email'),
            FieldPanel('telefono'),
            FieldPanel('ordine_appartenenza'),
        ], heading="Dati Avvocato"),
        MultiFieldPanel([
            FieldPanel('tribunale'),
            FieldPanel('sezione'),
            FieldPanel('giudice'),
            FieldPanel('tipo_udienza'),
        ], heading="Tribunale"),
        MultiFieldPanel([
            FieldPanel('numero_rg'),
            FieldPanel('parti_causa'),
            FieldPanel('data_udienza'),
            FieldPanel('ora_udienza'),
        ], heading="Dati Causa"),
        MultiFieldPanel([
            FieldPanel('attivita_richieste'),
            FieldPanel('note'),
        ], heading="Attività"),
        MultiFieldPanel([
            FieldPanel('status'),
            FieldPanel('esito_udienza'),
        ], heading="Stato"),
        InlinePanel('documents', label="📎 Documenti allegati", heading="Documenti allegati"),
    ]
    
    class Meta:
        verbose_name = "Richiesta domiciliazione"
        verbose_name_plural = "Richieste domiciliazione"
        ordering = ['-submit_time']
    
    def __str__(self):
        return f"{self.tribunale} - {self.data_udienza} - {self.numero_rg}"


class DomiciliazioniDocument(models.Model):
    """Documento allegato."""
    
    submission = ParentalKey(DomiciliazioniSubmission, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField("Documento", upload_to='domiciliazioni/%Y/%m/')
    original_filename = models.CharField("Nome file", max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    panels = [
        FieldPanel('file'),
        FieldPanel('original_filename', read_only=True),
    ]
    
    class Meta:
        verbose_name = "Documento allegato"
        verbose_name_plural = "Documenti allegati"
    
    def __str__(self):
        if self.file:
            return format_html('<a href="{}" target="_blank">📥 {}</a>', self.file.url, self.original_filename)
        return self.original_filename
