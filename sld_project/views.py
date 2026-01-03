"""
Views per le pagine legali (Privacy Policy e Termini e Condizioni).
Il contenuto viene caricato dal database (SiteSettings).
"""
import re
from django.shortcuts import render
from .models import SiteSettings


def _substitute_variables(content: str, settings: SiteSettings) -> str:
    """
    Sostituisce le variabili template nel contenuto HTML.
    Variabili supportate:
    - {{studio_name}}
    - {{lawyer_name}}
    - {{address}}
    - {{city}}
    - {{email}}
    - {{email_pec}}
    - {{phone}}
    """
    if not content:
        return ""
    
    substitutions = {
        "{{studio_name}}": settings.studio_name or "Studio Legale",
        "{{lawyer_name}}": settings.lawyer_name or "",
        "{{address}}": settings.address or "",
        "{{city}}": settings.city or "",
        "{{email}}": settings.email or "",
        "{{email_pec}}": settings.email_pec or "",
        "{{phone}}": settings.phone or "",
    }
    
    for var, value in substitutions.items():
        content = content.replace(var, value)
    
    return content


def privacy_view(request):
    """View per la Privacy Policy."""
    settings = SiteSettings.get_current()
    content = _substitute_variables(settings.privacy_policy, settings)
    
    return render(request, "pages/legal_page.html", {
        "page_title": "Privacy Policy",
        "page_subtitle": "Informativa ai sensi dell'art. 13 del Regolamento UE 2016/679 (GDPR)",
        "content": content,
    })


def terms_view(request):
    """View per i Termini e Condizioni."""
    settings = SiteSettings.get_current()
    content = _substitute_variables(settings.terms_conditions, settings)
    
    return render(request, "pages/legal_page.html", {
        "page_title": "Condizioni Generali di Contratto",
        "page_subtitle": "",
        "content": content,
    })


def custom_404_view(request, exception=None):
    """
    View personalizzata per la pagina 404.
    Include le aree di attività e gli articoli recenti.
    """
    from services.models import ServiceArea
    
    # Recupera le aree di attività
    service_areas = ServiceArea.objects.all()[:8]
    
    # Recupera gli articoli recenti
    recent_articles = []
    try:
        from articles.models import ArticlePage
        recent_articles = ArticlePage.objects.live().order_by('-first_published_at')[:3]
    except Exception:
        pass
    
    return render(request, "404.html", {
        "service_areas": service_areas,
        "recent_articles": recent_articles,
    }, status=404)


def custom_403_view(request, exception=None):
    """
    View personalizzata per la pagina 403 (Forbidden).
    Usata per errori CSRF, permessi insufficienti, ecc.
    """
    return render(request, "403.html", status=403)


def custom_500_view(request):
    """
    View personalizzata per la pagina 500 (Internal Server Error).
    Nota: non riceve exception, viene chiamata direttamente da Django.
    """
    return render(request, "500.html", status=500)
