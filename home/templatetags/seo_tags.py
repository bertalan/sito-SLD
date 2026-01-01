"""
Template tags per SEO e Schema.org JSON-LD.
"""
from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.simple_tag(takes_context=True)
def schema_org_jsonld(context):
    """Genera Schema.org JSON-LD per SEO."""
    request = context.get('request')
    page = context.get('page')
    
    if not page:
        return ''
    
    site_url = request.build_absolute_uri('/').rstrip('/')
    page_url = request.build_absolute_uri()
    
    # Schema base - Organization + LegalService
    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "LegalService",
                "@id": f"{site_url}/#legalservice",
                "name": "Studio Legale",
                "description": "Studio legale specializzato in diritto penale, famiglia e successioni, cittadinanza italiana e altre aree di pratica. Ufficio in Piazza G. Mazzini 72 a Lecce.",
                "url": site_url,
                "logo": f"{site_url}/static/images/dr_Logo.svg",
                "image": f"{site_url}/static/images/dr_Logo.svg",
                "email": "info@example.it",
                "telephone": "+39-320-7044664",
                "priceRange": "€€",
                "areaServed": [
                    {
                        "@type": "City",
                        "name": "Lecce"
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
                    "name": "Mario Rossi",
                    "jobTitle": "Avvocato",
                    "email": "info@example.it",
                    "telephone": "+39-320-7044664"
                },
                "location": [
                    {
                        "@type": "Place",
                        "@id": f"{site_url}/#lecce-office",
                        "name": "Studio Legale - Lecce",
                        "address": {
                            "@type": "PostalAddress",
                            "streetAddress": "Piazza Mazzini 72",
                            "addressLocality": "Lecce",
                            "postalCode": "73100",
                            "addressRegion": "LE",
                            "addressCountry": "IT"
                        },
                        "geo": {
                            "@type": "GeoCoordinates",
                            "latitude": 40.3516,
                            "longitude": 18.1718
                        },
                        "telephone": "+39-320-7044664",
                        "openingHoursSpecification": _get_opening_hours()
                    },
                ],
                "sameAs": [
                    "https://www.facebook.com/example/",
                    "https://twitter.com/avv_dr"
                ]
            },
            {
                "@type": "WebPage",
                "@id": page_url,
                "url": page_url,
                "name": page.seo_title if hasattr(page, 'seo_title') and page.seo_title else page.title,
                "description": page.search_description if hasattr(page, 'search_description') and page.search_description else "Studio Legale Avv. Mario Rossi",
                "isPartOf": {
                    "@type": "WebSite",
                    "@id": f"{site_url}/#website",
                    "url": site_url,
                    "name": "Studio Legale",
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
