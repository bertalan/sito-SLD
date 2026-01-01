"""
Context processors per template globali.
"""
from django.conf import settings


def global_settings(request):
    """Passa le impostazioni globali ai template."""
    return {
        # Analytics - GA4
        'ga4_measurement_id': getattr(settings, 'GA4_MEASUREMENT_ID', ''),
        # Analytics - Matomo
        'matomo_url': getattr(settings, 'MATOMO_URL', ''),
        'matomo_site_id': getattr(settings, 'MATOMO_SITE_ID', ''),
        # Studio info
        'studio_name': getattr(settings, 'STUDIO_NAME', ''),
        'studio_phone': getattr(settings, 'STUDIO_PHONE', ''),
        'studio_email': getattr(settings, 'STUDIO_EMAIL', ''),
    }
