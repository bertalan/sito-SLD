"""
Settings for running tests.
Uses StaticFilesStorage instead of ManifestStaticFilesStorage
to avoid needing collectstatic before running tests.
"""
from .dev import *

# Override STORAGES to use simple storage without manifest
# ManifestStaticFilesStorage requires collectstatic to generate staticfiles.json
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable rate limiting in tests
RATELIMIT_ENABLE = False
