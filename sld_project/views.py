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


def legacy_redirect_view(request, path=''):
    """
    Gestisce i redirect dalle vecchie URL /it/* estraendo keyword per la ricerca.
    
    Pattern supportati:
    - /it/News/titolo-articolo.html → estrae keyword dal titolo
    - /it/Ricerca.html?searchword=xxx → estrae dalla query string
    - /it/tag/nome-tag.html → estrae il nome del tag
    - /it/Aree-di-attivita/nome-area.html → redirect all'area corrispondente
    """
    from django.shortcuts import redirect
    from urllib.parse import unquote, urlencode
    import logging
    
    logger = logging.getLogger(__name__)
    keyword = None
    
    # 1. Prova a estrarre dalla query string (es: ?searchword=famiglia)
    searchword = request.GET.get('searchword', '') or request.GET.get('searchphrase', '')
    if searchword:
        # Pulisci: rimuovi // finali e caratteri strani
        keyword = searchword.strip('/').strip()
    
    # 2. Se non c'è query string, estrai dal path
    if not keyword and path:
        # Rimuovi estensione .html
        clean_path = path.replace('.html', '').replace('.htm', '')
        
        # Pattern: /it/tag/nome-tag → estrai "nome-tag"
        if clean_path.startswith('tag/'):
            keyword = clean_path[4:].replace('-', ' ').replace('_', ' ')
        
        # Pattern: /it/News/titolo-articolo → estrai parole dal titolo
        elif clean_path.startswith('News/'):
            title_part = clean_path[5:]
            # Converti trattini/underscore in spazi, rimuovi parole comuni
            keyword = _extract_keywords_from_slug(title_part)
        
        # Pattern: /it/Aree-di-attivita/nome → redirect diretto
        elif 'Aree-di-attivita' in clean_path or 'aree-attivita' in clean_path.lower():
            # Estrai nome area e cerca corrispondenza
            area_name = clean_path.split('/')[-1].replace('-', ' ')
            area_redirect = _find_service_area(area_name)
            if area_redirect:
                logger.info(f"Legacy redirect: /it/{path} → {area_redirect} (area match)")
                return redirect(area_redirect, permanent=True)
        
        # Pattern: /it/Ricerca.html → vai alla ricerca vuota
        elif 'Ricerca' in clean_path or 'ricerca' in clean_path:
            pass  # keyword resta None, andrà alla ricerca
        
        # Fallback: estrai parole significative dal path
        else:
            keyword = _extract_keywords_from_slug(clean_path)
    
    # Log per analytics
    referer = request.META.get('HTTP_REFERER', '')
    logger.info(f"Legacy redirect: /it/{path} → keyword='{keyword}' (referer: {referer[:100]})")
    
    # Redirect alla ricerca con keyword o alla pagina articoli
    if keyword and len(keyword) >= 2:
        # Usa legacy=1 per forzare ricerca OR (più permissiva con molte parole)
        search_url = f"/search/?{urlencode({'query': keyword, 'legacy': '1'})}"
        return redirect(search_url, permanent=False)  # 302 per non cacheare
    else:
        # Fallback: pagina articoli
        return redirect('/articoli-e-approfondimenti/', permanent=True)


def _extract_keywords_from_slug(slug):
    """
    Estrae keyword significative da uno slug URL.
    Rimuove parole comuni italiane e articoli.
    """
    import re
    
    # Decodifica URL encoding
    from urllib.parse import unquote
    slug = unquote(slug)
    
    # Sostituisci separatori con spazi
    text = re.sub(r'[-_/]', ' ', slug)
    
    # Rimuovi numeri isolati e caratteri speciali
    text = re.sub(r'\b\d+\b', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Split in parole
    words = text.lower().split()
    
    # Stopwords italiane comuni + categorie Joomla generiche
    stopwords = {
        'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una',
        'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
        'e', 'o', 'ma', 'che', 'non', 'è', 'sono', 'essere',
        'del', 'della', 'dello', 'dei', 'delle', 'degli',
        'al', 'alla', 'allo', 'ai', 'alle', 'agli',
        'dal', 'dalla', 'dallo', 'dai', 'dalle', 'dagli',
        'nel', 'nella', 'nello', 'nei', 'nelle', 'negli',
        'sul', 'sulla', 'sullo', 'sui', 'sulle', 'sugli',
        'come', 'quando', 'dove', 'perché', 'cosa', 'chi',
        'questo', 'questa', 'questi', 'queste', 'quello', 'quella',
        'più', 'meno', 'molto', 'poco', 'tutto', 'tutti',
        'altro', 'altri', 'altra', 'altre', 'stesso', 'stessa',
        'ogni', 'qualche', 'alcuni', 'alcune',
        'html', 'htm', 'php', 'asp', 'it', 'en', 'news', 'tag',
        'parte', 'articolo', 'pagina', 'sezione',
        # Categorie Joomla generiche
        'senza', 'categoria', 'uncategorised', 'uncategorized',
        'pareri', 'legali', 'consulenza',
    }
    
    # Filtra stopwords e parole troppo corte
    keywords = [w for w in words if w not in stopwords and len(w) >= 3]
    
    # Prendi le prime 4 parole significative
    return ' '.join(keywords[:4]) if keywords else None


def _find_service_area(area_name):
    """
    Cerca un'area di attività che corrisponda al nome.
    Restituisce l'URL se trovata, None altrimenti.
    """
    try:
        from services.models import ServiceArea
        
        # Normalizza il nome
        area_name_lower = area_name.lower()
        
        # Mappatura nomi vecchi → nuovi
        area_mapping = {
            'penale': 'diritto-penale',
            'civile': 'diritto-civile',
            'famiglia': 'diritto-di-famiglia',
            'lavoro': 'diritto-del-lavoro',
            'amministrativo': 'diritto-amministrativo',
            'consumatori': 'tutela-consumatori',
            'recupero crediti': 'recupero-crediti',
            'mediazione': 'mediazione-civile',
        }
        
        # Cerca match diretto o mappato
        for old_name, new_slug in area_mapping.items():
            if old_name in area_name_lower:
                area = ServiceArea.objects.filter(slug=new_slug).first()
                if area:
                    return area.url
        
        # Cerca per slug simile
        area = ServiceArea.objects.filter(slug__icontains=area_name_lower.replace(' ', '-')).first()
        if area:
            return area.url
            
    except Exception:
        pass
    
    return None
