from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField


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


class DomiciliazioniSubmission(models.Model):
    """Submission domiciliazione con allegati."""
    
    page = models.ForeignKey(DomiciliazioniPage, on_delete=models.CASCADE, related_name='submissions')
    form_data = models.JSONField()
    submit_time = models.DateTimeField(auto_now_add=True)
    nome_avvocato = models.CharField("Nome Avvocato", max_length=200)
    email = models.EmailField("Email")
    tribunale = models.CharField("Tribunale", max_length=100)
    tipo_udienza = models.CharField("Tipo udienza", max_length=100)
    data_udienza = models.DateField("Data udienza")
    note = models.TextField("Note", blank=True)
    
    class Meta:
        verbose_name = "Richiesta domiciliazione"
        verbose_name_plural = "Richieste domiciliazione"
        ordering = ['-submit_time']


class DomiciliazioniDocument(models.Model):
    """Documento allegato."""
    
    submission = models.ForeignKey(DomiciliazioniSubmission, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField("Documento", upload_to='domiciliazioni/%Y/%m/')
    original_filename = models.CharField("Nome file", max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Documento allegato"
        verbose_name_plural = "Documenti allegati"
    
    def __str__(self):
        return self.original_filename
