"""
Rate limiting utilities for protecting forms from spam/brute force.

Uses django-ratelimit to limit requests per IP address.
"""
from functools import wraps
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited


def get_client_ip(request):
    """
    Get the real client IP, considering proxy headers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP (client IP) from the chain
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ratelimit_json(rate='10/m', key='ip', block=True):
    """
    Rate limiting decorator that returns JSON error response.
    
    Args:
        rate: Rate limit string (e.g., '10/m' = 10 per minute, '100/h' = 100 per hour)
        key: Key to use for rate limiting ('ip', 'user', etc.)
        block: If True, block requests that exceed the limit
    
    Example usage:
        @ratelimit_json(rate='5/m')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Apply the ratelimit decorator
            limited_view = ratelimit(key=key, rate=rate, block=block, method='POST')(view_func)
            try:
                return limited_view(request, *args, **kwargs)
            except Ratelimited:
                return JsonResponse({
                    'error': 'Troppe richieste. Riprova tra qualche minuto.',
                    'retry_after': 60
                }, status=429)
        return wrapped_view
    return decorator


class RateLimitMixin:
    """
    Mixin for class-based views that adds rate limiting to POST requests.
    
    Set rate_limit class attribute to configure (default: '10/m').
    
    Example:
        class MyView(RateLimitMixin, View):
            rate_limit = '5/m'  # 5 requests per minute
            
            def post(self, request):
                ...
    """
    rate_limit = '10/m'  # Default: 10 requests per minute per IP
    
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            # Check rate limit
            from django_ratelimit.core import is_ratelimited
            
            ratelimited = is_ratelimited(
                request=request,
                group=self.__class__.__name__,
                key='ip',
                rate=self.rate_limit,
                increment=True
            )
            
            if ratelimited:
                return JsonResponse({
                    'error': 'Troppe richieste. Riprova tra qualche minuto.',
                    'retry_after': 60
                }, status=429)
        
        return super().dispatch(request, *args, **kwargs)


# Rate limits for different form types
RATE_LIMITS = {
    'booking': '10/m',       # 10 prenotazioni al minuto (per IP)
    'contact': '5/m',        # 5 messaggi contatto al minuto
    'domiciliazioni': '5/m', # 5 richieste domiciliazioni al minuto
    'login': '5/m',          # 5 tentativi login al minuto
    'api': '60/m',           # 60 richieste API al minuto
}
