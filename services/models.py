from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class ServiceArea(models.Model):
    """Area di pratica legale."""
    
    name = models.CharField("Nome", max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField("Icona", max_length=50, blank=True, help_text="Es: scale, gavel, shield")
    short_description = models.TextField("Descrizione breve", max_length=300)
    order = models.PositiveIntegerField("Ordine", default=0)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
        FieldPanel('icon'),
        FieldPanel('short_description'),
        FieldPanel('order'),
    ]
    
    class Meta:
        verbose_name = "Area di pratica"
        verbose_name_plural = "Aree di pratica"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class ServicesIndexPage(Page):
    """Pagina indice delle aree di pratica."""
    
    intro = RichTextField("Introduzione", blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    subpage_types = ['services.ServicePage']
    
    class Meta:
        verbose_name = "Pagina Aree di Pratica"
    
    def get_context(self, request):
        context = super().get_context(request)
        context['services'] = ServiceArea.objects.all()
        context['service_pages'] = ServicePage.objects.live().child_of(self)
        return context


class ServicePage(Page):
    """Pagina dettaglio singola area di pratica."""
    
    service_area = models.ForeignKey(
        ServiceArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='pages'
    )
    subtitle = models.CharField("Sottotitolo", max_length=200, blank=True)
    body = RichTextField("Contenuto")
    
    content_panels = Page.content_panels + [
        FieldPanel('service_area'),
        FieldPanel('subtitle'),
        FieldPanel('body'),
    ]
    
    parent_page_types = ['services.ServicesIndexPage']
    
    class Meta:
        verbose_name = "Pagina Servizio"
