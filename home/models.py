from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class HomePage(Page):
    """Homepage Studio Legale D'Onofrio."""
    
    # Hero
    hero_title = models.CharField("Titolo Hero", max_length=200, default="STUDIO LEGALE")
    hero_subtitle = models.CharField("Sottotitolo", max_length=200, default="D'ONOFRIO")
    hero_accent = models.CharField("Testo accent", max_length=100, default="GIUSTIZIA.")
    hero_description = RichTextField("Descrizione", blank=True)
    hero_location = models.CharField("Location", max_length=100, default="Lecce • Martina Franca")
    
    # Servizi
    services_title = models.CharField("Titolo Servizi", max_length=100, default="AREE DI PRATICA")
    services_subtitle = models.CharField("Sottotitolo", max_length=200, blank=True)
    
    # Chi siamo
    about_title = models.CharField("Titolo Chi Siamo", max_length=100, default="LO STUDIO")
    about_text = RichTextField("Testo", blank=True)
    
    # CTA
    cta_title = models.CharField("Titolo CTA", max_length=100, default="PARLIAMO")
    cta_text = models.CharField("Testo CTA", max_length=200, blank=True)
    cta_button_text = models.CharField("Pulsante", max_length=50, default="Prenota appuntamento")
    cta_button_url = models.CharField("URL", max_length=200, default="/prenota/")
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_accent'),
            FieldPanel('hero_description'),
            FieldPanel('hero_location'),
        ], heading="Hero"),
        MultiFieldPanel([
            FieldPanel('services_title'),
            FieldPanel('services_subtitle'),
        ], heading="Servizi"),
        MultiFieldPanel([
            FieldPanel('about_title'),
            FieldPanel('about_text'),
        ], heading="Chi Siamo"),
        MultiFieldPanel([
            FieldPanel('cta_title'),
            FieldPanel('cta_text'),
            FieldPanel('cta_button_text'),
            FieldPanel('cta_button_url'),
        ], heading="CTA"),
    ]
    
    class Meta:
        verbose_name = "Homepage"
    
    def get_context(self, request):
        from services.models import ServiceArea
        context = super().get_context(request)
        context['service_areas'] = ServiceArea.objects.all()[:6]
        return context
