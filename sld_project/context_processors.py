"""
Context processors per template globali.
"""
from django.conf import settings


def global_settings(request):
    """Passa le impostazioni globali ai template."""
    # Prima prova a leggere da SiteSettings (database)
    matomo_url = ''
    matomo_site_id = ''
    ga4_measurement_id = ''
    
    try:
        from sld_project.models import SiteSettings
        site_settings = SiteSettings.get_current()
        if site_settings.pk:
            matomo_url = site_settings.matomo_url or ''
            matomo_site_id = site_settings.matomo_site_id or ''
            ga4_measurement_id = site_settings.ga4_measurement_id or ''
    except Exception:
        pass
    
    # Fallback a variabili d'ambiente se non configurati in SiteSettings
    if not matomo_url:
        matomo_url = getattr(settings, 'MATOMO_URL', '')
    if not matomo_site_id:
        matomo_site_id = getattr(settings, 'MATOMO_SITE_ID', '')
    if not ga4_measurement_id:
        ga4_measurement_id = getattr(settings, 'GA4_MEASUREMENT_ID', '')
    
    return {
        # Analytics - GA4
        'ga4_measurement_id': ga4_measurement_id,
        # Analytics - Matomo
        'matomo_url': matomo_url,
        'matomo_site_id': matomo_site_id,
        # Studio info
        'studio_name': getattr(settings, 'STUDIO_NAME', ''),
        'studio_phone': getattr(settings, 'STUDIO_PHONE', ''),
        'studio_email': getattr(settings, 'STUDIO_EMAIL', ''),
    }
