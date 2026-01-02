"""
Template tags per SEO e Schema.org JSON-LD.
"""
from django import template
from django.conf import settings as django_settings
from django.utils.safestring import mark_safe
import json
import base64

register = template.Library()


@register.filter
def b64encode(value):
    """Codifica una stringa in base64 per offuscare email dallo spam."""
    if not value:
        return ''
    return base64.b64encode(str(value).encode('utf-8')).decode('utf-8')


def _get_studio_settings():
    """Recupera le impostazioni dello studio dal database."""
    try:
        from wagtail.models import Site
        from sld_project.models import SiteSettings
        site = Site.objects.filter(is_default_site=True).first()
        if site:
            studio_settings = SiteSettings.for_site(site)
            if studio_settings.pk:
                return {
                    'studio_name': studio_settings.studio_name,
                    'lawyer_name': studio_settings.lawyer_name,
                    'email': studio_settings.email,
                    'phone': studio_settings.phone,
                    'mobile_phone': studio_settings.mobile_phone,
                    'address': studio_settings.address,
                    'city': studio_settings.city,
                    'maps_lat': float(studio_settings.maps_lat),
                    'maps_lng': float(studio_settings.maps_lng),
                    'facebook_url': studio_settings.facebook_url,
                    'twitter_handle': studio_settings.twitter_handle,
                    'linkedin_url': studio_settings.linkedin_url,
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
        'maps_lat': 41.902782,
        'maps_lng': 12.496366,
        'facebook_url': '',
        'twitter_handle': '',
        'linkedin_url': '',
    }


@register.simple_tag(takes_context=True)
def schema_org_jsonld(context):
    """Genera Schema.org JSON-LD per SEO."""
    request = context.get('request')
    page = context.get('page')
    
    if not page:
        return ''
    
    studio = _get_studio_settings()
    site_url = request.build_absolute_uri('/').rstrip('/')
    page_url = request.build_absolute_uri()
    
    # Costruisci lista sameAs dai social disponibili
    same_as = []
    if studio.get('facebook_url'):
        same_as.append(studio['facebook_url'])
    if studio.get('twitter_handle'):
        handle = studio['twitter_handle'].lstrip('@')
        same_as.append(f"https://twitter.com/{handle}")
    if studio.get('linkedin_url'):
        same_as.append(studio['linkedin_url'])
    
    # Schema base - Organization + LegalService
    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "LegalService",
                "@id": f"{site_url}/#legalservice",
                "name": studio['studio_name'],
                "description": f"{studio['studio_name']} specializzato in diritto penale, famiglia e successioni, cittadinanza italiana e altre aree di pratica. Ufficio a {studio['city']}.",
                "url": site_url,
                "logo": f"{site_url}/static/images/StudioLegale.svg",
                "image": f"{site_url}/static/images/StudioLegale.svg",
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
                        "name": "Puglia"
                    }
                ],
                "knowsAbout": [
                    "Diritto Penale",
                    "Famiglia e Successioni",
                    "Privacy e GDPR",
                    "Contratti",
                    "Diritto dei Consumatori",
                    "Recupero Crediti",
                    "Risarcimento Danni",
                    "Infortunistica Stradale",
                    "Cittadinanza Italiana"
                ],
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
                "name": page.seo_title if hasattr(page, 'seo_title') and page.seo_title else page.title,
                "description": page.search_description if hasattr(page, 'search_description') and page.search_description else f"{studio['studio_name']} {studio['lawyer_name']}",
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
    
    # Aggiungi breadcrumb se non è homepage
    if page.url_path != '/home/':
        breadcrumbs = _get_breadcrumbs(page, site_url)
        if breadcrumbs:
            schema_data["@graph"].append(breadcrumbs)
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema_data, ensure_ascii=False, indent=2)}</script>')


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
