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
