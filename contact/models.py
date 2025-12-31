from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.snippets.models import register_snippet


class ContactFormField(AbstractFormField):
    """Campo form per la pagina contatti."""
    page = ParentalKey('ContactPage', on_delete=models.CASCADE, related_name='form_fields')


class ContactPage(AbstractEmailForm):
    """Pagina contatti con form integrato."""
    
    intro = RichTextField("Introduzione", blank=True)
    thank_you_text = RichTextField("Testo ringraziamento", blank=True)
    
    # Info studio
    address_lecce = models.CharField("Indirizzo Lecce", max_length=200, blank=True)
    address_martina = models.CharField("Indirizzo Martina Franca", max_length=200, blank=True)
    phone = models.CharField("Telefono", max_length=50, blank=True)
    mobile = models.CharField("Cellulare", max_length=50, blank=True)
    email = models.EmailField("Email", blank=True)
    pec = models.EmailField("PEC", blank=True)
    
    # Coordinate mappa OpenStreetMap
    lecce_lat = models.FloatField("Latitudine Lecce", default=40.3516)
    lecce_lng = models.FloatField("Longitudine Lecce", default=18.1718)
    martina_lat = models.FloatField("Latitudine Martina Franca", default=40.7051)
    martina_lng = models.FloatField("Longitudine Martina Franca", default=17.3361)
    
    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('intro'),
        InlinePanel('form_fields', label="Campi del form"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldPanel('address_lecce'),
            FieldPanel('address_martina'),
            FieldPanel('phone'),
            FieldPanel('mobile'),
            FieldPanel('email'),
            FieldPanel('pec'),
        ], heading="Contatti"),
        MultiFieldPanel([
            FieldPanel('lecce_lat'),
            FieldPanel('lecce_lng'),
            FieldPanel('martina_lat'),
            FieldPanel('martina_lng'),
        ], heading="Coordinate mappa"),
        MultiFieldPanel([
            FieldPanel('to_address'),
            FieldPanel('from_address'),
            FieldPanel('subject'),
        ], heading="Email"),
    ]
    
    class Meta:
        verbose_name = "Pagina Contatti"


@register_snippet
class SocialLink(models.Model):
    """Link social media."""
    
    PLATFORMS = [
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter/X'),
        ('linkedin', 'LinkedIn'),
    ]
    
    platform = models.CharField("Piattaforma", max_length=20, choices=PLATFORMS)
    url = models.URLField("URL")
    is_active = models.BooleanField("Attivo", default=True)
    
    panels = [
        FieldPanel('platform'),
        FieldPanel('url'),
        FieldPanel('is_active'),
    ]
    
    class Meta:
        verbose_name = "Link Social"
        verbose_name_plural = "Link Social"
    
    def __str__(self):
        return self.get_platform_display()
