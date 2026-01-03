"""
Sistema articoli/blog collegato alle aree di attività.
Segue i pattern Wagtail: Page models, Snippets, ParentalManyToManyField.
"""
from django.db import models
from django.utils.html import strip_tags
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.search import index
from modelcluster.fields import ParentalManyToManyField
from services.models import ServiceArea


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORIE ARTICOLI (Snippet)
# ═══════════════════════════════════════════════════════════════════════════

@register_snippet
class ArticleCategory(models.Model):
    """Categoria articolo: News, Pareri, Guide."""
    
    name = models.CharField("Nome", max_length=50)
    slug = models.SlugField(unique=True)
    icon = models.CharField(
        "Icona", 
        max_length=50, 
        default="file-text",
        help_text="Icona Lucide (es: newspaper, message-square, book-open)"
    )
    order = models.PositiveIntegerField("Ordine", default=0)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
        FieldPanel('icon'),
        FieldPanel('order'),
    ]
    
    class Meta:
        verbose_name = "Categoria articolo"
        verbose_name_plural = "Categorie articoli"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


# ═══════════════════════════════════════════════════════════════════════════
# PAGINA INDICE ARTICOLI
# ═══════════════════════════════════════════════════════════════════════════

class ArticleIndexPage(Page):
    """Pagina indice degli articoli (/articoli/)."""
    
    intro = RichTextField("Introduzione", blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    subpage_types = ['articles.ArticlePage']
    max_count = 1  # Solo una pagina indice
    
    class Meta:
        verbose_name = "Pagina Indice Articoli"
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Filtro per categoria
        category_slug = request.GET.get('categoria')
        articles = ArticlePage.objects.live().child_of(self).order_by('-first_published_at')
        
        if category_slug:
            articles = articles.filter(category__slug=category_slug)
        
        context['articles'] = articles
        context['categories'] = ArticleCategory.objects.all()
        context['current_category'] = category_slug
        return context


# ═══════════════════════════════════════════════════════════════════════════
# PAGINA SINGOLO ARTICOLO
# ═══════════════════════════════════════════════════════════════════════════

class ArticlePage(Page):
    """Singolo articolo del blog legale."""
    
    # Categoria
    category = models.ForeignKey(
        ArticleCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name="Categoria"
    )
    
    # Aree di attività collegate (ManyToMany via Wagtail)
    service_areas = ParentalManyToManyField(
        ServiceArea,
        blank=True,
        related_name='articles',
        verbose_name="Aree di attività"
    )
    
    # Contenuto
    subtitle = models.CharField(
        "Sottotitolo", 
        max_length=300, 
        blank=True,
        help_text="Breve descrizione per SEO e anteprime"
    )
    body = RichTextField("Contenuto")
    
    # Immagine di copertina (opzionale)
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Immagine copertina"
    )
    
    # Metadata
    reading_time = models.PositiveIntegerField(
        "Tempo di lettura (min)", 
        default=1,
        help_text="Calcolato automaticamente al salvataggio"
    )
    
    # Pannelli admin
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('category'),
            FieldPanel('service_areas'),
        ], heading="Classificazione"),
        FieldPanel('subtitle'),
        FieldPanel('cover_image'),
        FieldPanel('body'),
    ]
    
    promote_panels = Page.promote_panels + [
        FieldPanel('reading_time', read_only=True),
    ]
    
    # Indicizzazione ricerca
    search_fields = Page.search_fields + [
        index.SearchField('subtitle'),
        index.SearchField('body'),
    ]
    
    parent_page_types = ['articles.ArticleIndexPage']
    
    class Meta:
        verbose_name = "Articolo"
        verbose_name_plural = "Articoli"
    
    def save(self, *args, **kwargs):
        # Calcola tempo di lettura (200 parole/minuto)
        if self.body:
            word_count = len(strip_tags(self.body).split())
            self.reading_time = max(1, round(word_count / 200))
        super().save(*args, **kwargs)
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Articoli correlati (stessa categoria o area di pratica)
        related = ArticlePage.objects.live().exclude(pk=self.pk)
        
        if self.service_areas.exists():
            related = related.filter(service_areas__in=self.service_areas.all()).distinct()
        elif self.category:
            related = related.filter(category=self.category)
        
        context['related_articles'] = related[:3]
        return context


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_articles_for_service_area(service_area, limit=6):
    """Ottiene gli articoli collegati a un'area di pratica."""
    return ArticlePage.objects.live().filter(
        service_areas=service_area
    ).order_by('-first_published_at')[:limit]
