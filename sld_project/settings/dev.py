from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
# In development legge da .env, fallback a valore insecure solo per test locali
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-only-do-not-use-in-production')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

# In dev, usa console backend a meno che non sia specificato diversamente via env
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')


try:
    from .local import *
except ImportError:
    pass
