from django.db import models
from django.http import HttpResponse
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
    
    # Info studio - ora gestite da SiteSettings
    # I campi seguenti sono deprecati e verranno rimossi in una migrazione futura
    
    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('intro'),
        InlinePanel('form_fields', label="Campi del form"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldPanel('to_address'),
            FieldPanel('from_address'),
            FieldPanel('subject'),
        ], heading="Email"),
    ]
    
    class Meta:
        verbose_name = "Pagina Contatti"
    
    def serve(self, request, *args, **kwargs):
        """Override serve to add rate limiting for spam protection."""
        from django_ratelimit.core import is_ratelimited
        from sld_project.ratelimit import RATE_LIMITS
        
        if request.method == 'POST':
            # Rate limiting: 5 messaggi/minuto per IP
            if is_ratelimited(
                request=request,
                group='contact',
                key='ip',
                rate=RATE_LIMITS['contact'],
                increment=True
            ):
                return HttpResponse(
                    '<html><body><h1>Troppe richieste</h1>'
                    '<p>Hai inviato troppi messaggi. Riprova tra qualche minuto.</p>'
                    '</body></html>',
                    status=429,
                    content_type='text/html'
                )
        
        # Delega al metodo serve originale di AbstractEmailForm
        return super().serve(request, *args, **kwargs)


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
