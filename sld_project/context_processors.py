"""
Context processors per template globali.
"""
from django.conf import settings


def global_settings(request):
    """Passa le impostazioni globali ai template."""
    return {
        'ga4_measurement_id': getattr(settings, 'GA4_MEASUREMENT_ID', ''),
        'studio_name': getattr(settings, 'STUDIO_NAME', ''),
        'studio_phone': getattr(settings, 'STUDIO_PHONE', ''),
        'studio_email': getattr(settings, 'STUDIO_EMAIL', ''),
    }
