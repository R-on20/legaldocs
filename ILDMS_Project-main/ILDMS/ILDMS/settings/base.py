from pathlib import Path
import os
from dotenv import load_dotenv


# ============================================================
# BASE DIRECTORY
# ============================================================

# base.py is inside ILDMS/settings/
# BASE_DIR should point to the project root containing manage.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    raise ValueError(
        "DJANGO_SECRET_KEY is not set. "
        "Add it to your environment variables or .env file."
    )


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # Project apps
    'documents',
    'main',
    'accounts',
    'analytics',

    # Third-party apps
    'ckeditor',
]


# ============================================================
# CRISPY FORMS
# ============================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom security middleware
    'accounts.middleware.SecurityHeadersMiddleware',

    # Keep disabled until reviewed
    # 'accounts.middleware.RequestValidationMiddleware',
    # 'accounts.middleware.SessionSecurityMiddleware',
]


# ============================================================
# URLS / WSGI / ASGI
# ============================================================

ROOT_URLCONF = 'ILDMS.urls'

WSGI_APPLICATION = 'ILDMS.wsgi.application'
ASGI_APPLICATION = 'ILDMS.asgi.application'


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Custom context processor
                'documents.context_processors.document_permissions',
            ],
        },
    },
]


# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# AUTHENTICATION
# ============================================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_USER_MODEL = 'main.User'


# ============================================================
# AUTH URLS
# ============================================================

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'documents:document_list'
LOGOUT_REDIRECT_URL = 'accounts:home'


# ============================================================
# SESSION SETTINGS
# ============================================================

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 43200  # 12 hours

SESSION_SAVE_EVERY_REQUEST = True


# ============================================================
# FILE UPLOAD SETTINGS
# ============================================================

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

FILE_UPLOAD_PERMISSIONS = 0o640
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o750


# ============================================================
# CKEDITOR
# ============================================================

CKEDITOR_UPLOAD_PATH = "ckeditor/new_docs/"

CKEDITOR_ALLOW_NONIMAGE_FILES = False
CKEDITOR_RESTRICT_BY_USER = True
CKEDITOR_BROWSE_SHOW_DIRS = False


CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',

        'toolbar_Custom': [
            ['Undo', 'Redo'],
            ['Bold', 'Italic', 'Underline', 'Strike'],
            ['Font', 'FontSize'],
            ['TextColor', 'BGColor'],
            ['NumberedList', 'BulletedList'],
            ['Outdent', 'Indent', 'Blockquote'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight'],
            ['Link', 'Unlink'],
            ['Table', 'HorizontalRule'],
            ['Maximize', 'Source'],
        ],

        'height': 600,
        'width': 1000,

        'removePlugins': 'image,flash,iframe',
        'extraPlugins': '',

        'allowedContent': True,

        'removeDialogTabs': 'image:advanced;image:Link',

        'forcePasteAsPlainText': True,
        'pasteFromWordRemoveFontStyles': True,
        'pasteFromWordRemoveStyles': True,

        'disableNativeSpellChecker': False,

        'removeFormatAttributes':
            'class,style,lang,width,height,align,hspace,valign',

        'removeFormatTags':
            'b,big,code,del,dfn,em,font,i,ins,kbd,q,samp,'
            'small,span,strike,strong,sub,sup,tt,u,var',

        'format_tags': 'p;h1;h2;h3;h4;h5;h6',
    },

    'restricted': {
        'toolbar': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList'],
            ['Link', 'Unlink'],
        ],

        'height': 300,
        'width': 600,

        'removePlugins': 'image,flash,iframe,forms',

        'forcePasteAsPlainText': True,

        'disableNativeSpellChecker': False,
    }
}


# ============================================================
# OPENAI / AI SEARCH
# ============================================================

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

OPENAI_MODEL = os.getenv(
    'OPENAI_MODEL',
    'gpt-3.5-turbo'
)

AI_SEARCH_ENABLED = (
    os.getenv('AI_SEARCH_ENABLED', 'True').lower() == 'true'
)


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')

if GMAIL_APP_PASSWORD and EMAIL_HOST_USER:

    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587

    EMAIL_USE_TLS = True

    EMAIL_HOST_PASSWORD = GMAIL_APP_PASSWORD

    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

else:

    # Development-safe fallback
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

    DEFAULT_FROM_EMAIL = (
        EMAIL_HOST_USER
        or 'noreply@localhost'
    )


# ============================================================
# LOGGING
# ============================================================

LOGS_DIR = BASE_DIR / 'logs'

LOGS_DIR.mkdir(exist_ok=True)


LOGGING = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {

        'verbose': {
            'format':
                '{levelname} {asctime} '
                '{module} {process:d} '
                '{thread:d} {message}',

            'style': '{',
        },

        'security': {
            'format':
                '[SECURITY] {asctime} '
                '{levelname} {message}',

            'style': '{',
        },
    },

    'handlers': {

        'file': {
            'level': 'INFO',

            'class': 'logging.FileHandler',

            'filename': str(
                LOGS_DIR / 'django.log'
            ),

            'formatter': 'verbose',
        },

        'security_file': {
            'level': 'WARNING',

            'class': 'logging.FileHandler',

            'filename': str(
                LOGS_DIR / 'security.log'
            ),

            'formatter': 'security',
        },

        'console': {
            'level': 'DEBUG',

            'class': 'logging.StreamHandler',

            'formatter': 'verbose',
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },

    'loggers': {

        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },

        'documents.security_utils': {
            'handlers': [
                'security_file',
                'console',
            ],

            'level': 'WARNING',

            'propagate': False,
        },

        'accounts.middleware': {
            'handlers': [
                'security_file',
                'console',
            ],

            'level': 'WARNING',

            'propagate': False,
        },
    },
}