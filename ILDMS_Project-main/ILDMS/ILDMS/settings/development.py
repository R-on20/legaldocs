from .base import *


# ============================================================
# DEVELOPMENT SETTINGS
# ============================================================

DEBUG = True


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]


# ============================================================
# DEVELOPMENT EMAIL
# ============================================================

# Always print emails to the terminal during development.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ============================================================
# DEVELOPMENT LOGGING
# ============================================================

LOGGING['root']['level'] = 'DEBUG'

LOGGING['loggers']['django']['level'] = 'DEBUG'


# ============================================================
# DEVELOPMENT SECURITY
# ============================================================

# HTTPS is not being enforced locally.
SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False