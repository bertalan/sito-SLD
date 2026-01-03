"""
Template tags per SEO e Schema.org JSON-LD.
"""
import re
from django import template
from django.conf import settings as django_settings
from django.utils.safestring import mark_safe
import json
import base64

register = template.Library()


# ═══════════════════════════════════════════════════════════════════════════
# COLORI BRAND
# ═══════════════════════════════════════════════════════════════════════════

# Colori di default (fallback se SiteSettings non disponibile)
DEFAULT_BRAND_COLORS = {
    'brand-black': '#0a0a0a',
    'brand-dark': '#1a1a1a',
    'brand-gray': '#6b7280',
    'brand-silver': '#f5f5f5',
    'brand-white': '#ffffff',
    'brand-accent': '#e91e63',
    'brand-accent-hover': '#be185d',
}


def _get_brand_colors():
    """Helper per ottenere i colori brand dal database o default."""
    try:
        from sld_project.models import SiteSettings
        settings = SiteSettings.get_current()
        return settings.get_brand_colors()
    except Exception:
        return DEFAULT_BRAND_COLORS


@register.simple_tag(takes_context=True)
def tailwind_brand_config(context):
    """
    Genera la configurazione Tailwind con i colori dal database.
    
    Uso nel template:
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {% tailwind_brand_config %},
                    fontFamily: {
                        'sans': ['Inter', 'system-ui', 'sans-serif'],
                    }
                }
            }
        }
    </script>
    """
    return mark_safe(json.dumps(_get_brand_colors()))


@register.simple_tag(takes_context=True)
def brand_css_variables(context):
    """
    Genera le CSS custom properties per i colori brand.
    Da usare in un tag <style> nel <head>.
    
    Uso nel template:
    <style>
        :root {
            {% brand_css_variables %}
        }
    </style>
    
    Genera:
        --brand-black: #0a0a0a;
        --brand-accent: #e91e63;
        ...
    """
    colors = _get_brand_colors()
    css_vars = []
    for name, value in colors.items():
        css_vars.append(f"--{name}: {value};")
    return mark_safe("\n            ".join(css_vars))


@register.simple_tag(takes_context=True)
def brand_accent_color(context):
    """
    Ritorna il colore accent per uso inline (es: style="background-color: {% brand_accent_color %};")
    """
    colors = _get_brand_colors()
    return colors.get('brand-accent', DEFAULT_BRAND_COLORS['brand-accent'])


@register.filter
def b64encode(value):
    """Codifica una stringa in base64 per offuscare email dallo spam."""
    if not value:
        return ''
    return base64.b64encode(str(value).encode('utf-8')).decode('utf-8')


@register.filter
def format_accent_apostrophe(value, color_class="text-brand-accent"):
    """
    Formatta un testo colorando l'apostrofo con una classe CSS.
    Es: "D'ONOFRIO" -> "D<span class='text-brand-accent'>'</span>ONOFRIO"
    """
    if not value:
        return ''
    # Cerca apostrofo (sia ' che ')
    formatted = re.sub(
        r"(['''])",
        f'<span class="{color_class}">\\1</span>',
        str(value)
    )
    return mark_safe(formatted)


@register.simple_tag(takes_context=True)
def render_footer_studio_name(context):
    """
    Renderizza il nome dello studio nel footer con formattazione speciale.
    Usa i campi hero_txt_studio, hero_txt_legale e hero_txt_accent dalla HomePage.
    Output: <span class="text-brand-gray">STUDIO<br/>LEGALE</span><br/>
            <span class="text-white">D</span><span class="text-brand-accent">'</span><span class="text-white">ONOFRIO</span>
    """
    try:
        from home.models import HomePage
        home = HomePage.objects.live().first()
        if not home:
            return mark_safe('STUDIO LEGALE')
        
        # Prendi i valori dai campi
        txt_studio = home.hero_txt_studio or "STUDIO"
        txt_legale = home.hero_txt_legale or "LEGALE"
        txt_accent = home.hero_txt_accent or ""
        
        # Formatta STUDIO e LEGALE come righe separate in grigio
        studio_html = f'<span class="text-brand-gray">{txt_studio.upper()}<br/>{txt_legale.upper()}</span>'
        
        # Formatta il cognome con apostrofo colorato
        if txt_accent:
            # Trova l'apostrofo e colora
            accent_html = re.sub(
                r"(['''])",
                '</span><span class="text-brand-accent">\\1</span><span class="text-white">',
                txt_accent.upper()
            )
            accent_html = f'<span class="text-white">{accent_html}</span>'
            return mark_safe(f'{studio_html}<br/>{accent_html}')
        
        return mark_safe(studio_html)
    except Exception:
        return mark_safe('STUDIO LEGALE')


@register.simple_tag(takes_context=True)
def get_logo_url(context):
    """Ritorna l'URL del logo (da SiteSettings o fallback a statico)."""
    request = context.get('request')
    if not request:
        return '/static/images/StudioLegale.svg'
    
    try:
        from wagtail.models import Site
        from sld_project.models import SiteSettings
        site = Site.objects.filter(is_default_site=True).first()
        if site:
            settings = SiteSettings.for_site(site)
            if settings.pk and settings.logo:
                logo_url = settings.logo.file.url
                # Rendi URL assoluto
                if logo_url.startswith('/'):
                    return f"{request.scheme}://{request.get_host()}{logo_url}"
                return logo_url
    except Exception:
        pass
    
    return f"{request.scheme}://{request.get_host()}/static/images/StudioLegale.svg"


def _get_studio_settings():
    """Recupera le impostazioni dello studio dal database."""
    try:
        from wagtail.models import Site
        from sld_project.models import SiteSettings
        site = Site.objects.filter(is_default_site=True).first()
        if site:
            studio_settings = SiteSettings.for_site(site)
            if studio_settings.pk:
                # Ottieni URL logo se caricato
                logo_url = None
                if studio_settings.logo:
                    try:
                        logo_url = studio_settings.logo.url
                    except Exception:
                        pass
                return {
                    'studio_name': studio_settings.studio_name,
                    'lawyer_name': studio_settings.lawyer_name,
                    'email': studio_settings.email,
                    'phone': studio_settings.phone,
                    'mobile_phone': studio_settings.mobile_phone,
                    'address': studio_settings.address,
                    'city': studio_settings.city,
                    'province': studio_settings.province,
                    'maps_lat': float(studio_settings.maps_lat),
                    'maps_lng': float(studio_settings.maps_lng),
                    'facebook_url': studio_settings.facebook_url,
                    'x_url': studio_settings.x_url,
                    'linkedin_url': studio_settings.linkedin_url,
                    'logo_url': logo_url,
                }
    except Exception:
        pass
    
    # Fallback a django settings
    return {
        'studio_name': getattr(django_settings, 'STUDIO_NAME', 'Studio Legale'),
        'lawyer_name': getattr(django_settings, 'LAWYER_NAME', 'Avv. Mario Rossi'),
        'email': getattr(django_settings, 'STUDIO_EMAIL', 'info@example.com'),
        'phone': getattr(django_settings, 'STUDIO_PHONE', '+39 06 12345678'),
        'mobile_phone': getattr(django_settings, 'STUDIO_MOBILE', ''),
        'address': getattr(django_settings, 'STUDIO_ADDRESS', 'Via Roma, 1 - 00100 Roma'),
        'city': getattr(django_settings, 'STUDIO_CITY', 'Roma'),
        'province': getattr(django_settings, 'STUDIO_PROVINCE', 'Lazio'),
        'maps_lat': 41.902782,
        'maps_lng': 12.496366,
        'facebook_url': '',
        'x_url': '',
        'linkedin_url': '',
        'logo_url': None,
    }


@register.simple_tag(takes_context=True)
def schema_org_jsonld(context):
    """Genera Schema.org JSON-LD per SEO."""
    request = context.get('request')
    page = context.get('page')
    
    if not request:
        return ''
    
    studio = _get_studio_settings()
    site_url = request.build_absolute_uri('/').rstrip('/')
    page_url = request.build_absolute_uri()
    
    # Costruisci lista sameAs dai social disponibili
    same_as = []
    if studio.get('facebook_url'):
        same_as.append(studio['facebook_url'])
    if studio.get('x_url'):
        same_as.append(studio['x_url'])
    if studio.get('linkedin_url'):
        same_as.append(studio['linkedin_url'])
    
    # Recupera aree di attività per knowsAbout
    knows_about = _get_knows_about()
    
    # Schema base - Organization + LegalService
    logo_url = studio.get('logo_url') or f"{site_url}/static/images/StudioLegale.svg"
    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "LegalService",
                "@id": f"{site_url}/#legalservice",
                "name": studio['studio_name'],
                "description": f"{studio['studio_name']} specializzato in diritto penale, famiglia e successioni, cittadinanza italiana e altre aree di attività. Ufficio a {studio['city']}.",
                "url": site_url,
                "logo": logo_url,
                "image": logo_url,
                "email": studio['email'],
                "telephone": studio['phone'],
                "priceRange": "€€",
                "areaServed": [
                    {
                        "@type": "City",
                        "name": studio['city']
                    },
                    {
                        "@type": "AdministrativeArea",
                        "name": studio['province']
                    }
                ],
                "knowsAbout": knows_about,
                "employee": {
                    "@type": "Person",
                    "name": studio['lawyer_name'].replace('Avv. ', ''),
                    "jobTitle": "Avvocato",
                    "email": studio['email'],
                    "telephone": studio['phone']
                },
                "location": [
                    {
                        "@type": "Place",
                        "@id": f"{site_url}/#office",
                        "name": f"{studio['studio_name']} - {studio['city']}",
                        "address": {
                            "@type": "PostalAddress",
                            "streetAddress": studio['address'],
                            "addressLocality": studio['city'],
                            "addressCountry": "IT"
                        },
                        "geo": {
                            "@type": "GeoCoordinates",
                            "latitude": studio['maps_lat'],
                            "longitude": studio['maps_lng']
                        },
                        "telephone": studio['phone'],
                        "openingHoursSpecification": _get_opening_hours()
                    },
                ],
                "sameAs": same_as
            },
            {
                "@type": "WebPage",
                "@id": page_url,
                "url": page_url,
                "name": (page.seo_title if hasattr(page, 'seo_title') and page.seo_title else page.title) if page else studio['studio_name'],
                "description": (page.search_description if hasattr(page, 'search_description') and page.search_description else f"{studio['studio_name']} {studio['lawyer_name']}") if page else f"{studio['studio_name']} - {studio['city']}",
                "isPartOf": {
                    "@type": "WebSite",
                    "@id": f"{site_url}/#website",
                    "url": site_url,
                    "name": studio['studio_name'],
                    "publisher": {
                        "@id": f"{site_url}/#legalservice"
                    }
                }
            }
        ]
    }
    
    # Aggiungi breadcrumb se non è homepage e se page esiste
    if page and hasattr(page, 'url_path') and page.url_path != '/home/':
        breadcrumbs = _get_breadcrumbs(page, site_url)
        if breadcrumbs:
            schema_data["@graph"].append(breadcrumbs)
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema_data, ensure_ascii=False, indent=2)}</script>')


def _get_knows_about():
    """Recupera le aree di attività per il campo knowsAbout."""
    try:
        from services.models import ServiceArea
        areas = ServiceArea.objects.all().order_by('order', 'name')
        if areas.exists():
            return [area.name for area in areas]
    except Exception:
        pass
    
    # Fallback se non ci sono aree
    return [
        "Diritto Penale",
        "Famiglia e Successioni", 
        "Contratti",
        "Recupero Crediti"
    ]


def _get_opening_hours():
    """Recupera orari di apertura da AvailabilityRule."""
    try:
        from booking.models import AvailabilityRule
        
        rules = AvailabilityRule.objects.filter(is_active=True).order_by('weekday', 'start_time')
        
        # Mappa giorni della settimana per Schema.org
        day_mapping = {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
            6: 'Sunday'
        }
        
        opening_hours = []
        current_days = []
        current_times = None
        
        for rule in rules:
            day_name = day_mapping.get(rule.weekday)
            times = f"{rule.start_time.strftime('%H:%M')}:{rule.end_time.strftime('%H:%M')}"
            
            if current_times == times:
                current_days.append(day_name)
            else:
                if current_days and current_times:
                    opens, closes = current_times.split(':')[:2], current_times.split(':')[2:]
                    opening_hours.append({
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": current_days if len(current_days) > 1 else current_days[0],
                        "opens": f"{opens[0]}:{opens[1]}",
                        "closes": f"{closes[0]}:{closes[1]}"
                    })
                current_days = [day_name]
                current_times = times
        
        # Aggiungi l'ultimo gruppo
        if current_days and current_times:
            opens, closes = current_times.split(':')[:2], current_times.split(':')[2:]
            opening_hours.append({
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": current_days if len(current_days) > 1 else current_days[0],
                "opens": f"{opens[0]}:{opens[1]}",
                "closes": f"{closes[0]}:{closes[1]}"
            })
        
        return opening_hours if opening_hours else []
    except Exception:
        # Fallback se non ci sono regole
        return []


def _get_breadcrumbs(page, site_url):
    """Genera breadcrumb list per Schema.org."""
    ancestors = page.get_ancestors(inclusive=True).live().public().specific()
    
    if len(ancestors) <= 1:
        return None
    
    items = []
    for i, ancestor in enumerate(ancestors, 1):
        # Salta Root
        if ancestor.depth == 1:
            continue
        
        items.append({
            "@type": "ListItem",
            "position": i,
            "name": ancestor.title,
            "item": site_url + ancestor.url
        })
    
    if not items:
        return None
    
    return {
        "@type": "BreadcrumbList",
        "itemListElement": items
    }
