from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-2e19_40bu4$)(re90p+uta_wtsw(7(r%t*blg8e=hbwydawoml"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

# In dev, usa console backend a meno che non sia specificato diversamente via env
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')


try:
    from .local import *
except ImportError:
    pass
