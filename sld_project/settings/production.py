"""
Production settings for sld_project.

Security headers and HTTPS enforcement enabled.
"""
from .base import *

DEBUG = False

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

# HTTPS/SSL
SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Trust proxy headers
SESSION_COOKIE_SECURE = True  # Only send session cookie over HTTPS
CSRF_COOKIE_SECURE = True  # Only send CSRF cookie over HTTPS

# HSTS (HTTP Strict Transport Security)
# Tells browsers to only use HTTPS for this domain
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Apply to all subdomains
SECURE_HSTS_PRELOAD = True  # Allow preloading in browser HSTS lists

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME type sniffing
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking (stricter than SAMEORIGIN)

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cross-Origin headers (set via SecurityMiddleware)
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT SECURITY POLICY (CSP)
# ═══════════════════════════════════════════════════════════════════════════════
# Note: CSP is implemented via custom middleware below, not django-csp
# This allows fine-grained control without additional dependencies

CSP_POLICY = {
    "default-src": "'self'",
    "script-src": "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://js.stripe.com https://www.paypal.com https://www.google.com https://www.gstatic.com",
    "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com",
    "font-src": "'self' https://fonts.gstatic.com",
    "img-src": "'self' data: https: blob:",
    "connect-src": "'self' https://api.stripe.com https://www.paypal.com",
    "frame-src": "https://js.stripe.com https://www.paypal.com https://www.google.com",
    "object-src": "'none'",
    "base-uri": "'self'",
    "form-action": "'self' https://www.paypal.com",
}

# Build CSP header string
CSP_HEADER = "; ".join(f"{key} {value}" for key, value in CSP_POLICY.items())

# Custom middleware to add CSP header
class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        # Don't add CSP to admin pages (can break functionality)
        if not request.path.startswith('/admin/') and not request.path.startswith('/cms/'):
            response['Content-Security-Policy'] = CSP_HEADER
        # Additional security headers
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response

# Insert CSP middleware after SecurityMiddleware
MIDDLEWARE.insert(
    MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
    'sld_project.settings.production.ContentSecurityPolicyMiddleware'
)

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE - Use environment variable
# ═══════════════════════════════════════════════════════════════════════════════
import dj_database_url
import os

if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }

try:
    from .local import *
except ImportError:
    pass
