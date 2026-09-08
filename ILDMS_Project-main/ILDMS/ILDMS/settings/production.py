from .base import *


# ============================================================
# PRODUCTION SETTINGS
# ============================================================

DEBUG = False


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]

if not ALLOWED_HOSTS:
    raise ValueError(
        "DJANGO_ALLOWED_HOSTS must be configured in production."
    )


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]


# ============================================================
# HTTPS / SECURITY
# ============================================================

SECURE_SSL_REDIRECT = True

SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https',
)

SECURE_HSTS_SECONDS = 31536000

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

X_FRAME_OPTIONS = 'DENY'


# ============================================================
# SECURE COOKIES
# ============================================================

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'


# ============================================================
# EMAIL
# ============================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.getenv(
    'EMAIL_HOST',
    'smtp.gmail.com'
)

EMAIL_PORT = int(
    os.getenv(
        'EMAIL_PORT',
        '587'
    )
)

EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv(
    'EMAIL_HOST_USER'
)

EMAIL_HOST_PASSWORD = os.getenv(
    'GMAIL_APP_PASSWORD'
)

DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    EMAIL_HOST_USER
)


# ============================================================
# STATIC FILES
# ============================================================

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ============================================================
# LOGGING
# ============================================================

LOGGING['root']['level'] = 'INFO'

LOGGING['loggers']['django']['level'] = 'INFO'