"""
Django settings for Ecommerce project.
"""

from pathlib import Path
from datetime import timedelta 
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/


# Read settings from the .env file.
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')


# No default on purpose: if it's missing, Django should fail loudly.
SECRET_KEY = env('SECRET_KEY')

DEBUG = env.bool('DEBUG',default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS',default=[])

# Full origins (with https://) allowed to submit forms, such as the admin login
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'rest_framework_simplejwt.token_blacklist',

    # Internal Core Subsystems
    'store',
    'accounts',
    'cart',
    'order'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # Serves static files (admin CSS/JS) in production, where runserver isn't used
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    # Django native middleware for language translation processing
    'django.middleware.locale.LocaleMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom middleware to handle user language preference
    'Ecommerce.middlewares.AppPreferencesMiddleware',
]

ROOT_URLCONF = 'Ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Ecommerce.wsgi.application'


# Read the connection from DATABASE_URL, postgres://user:pass@host:5432/name
DATABASES = {
    'default': env.db('DATABASE_URL'),
}


# Custom user model configuration
AUTH_USER_MODEL = 'accounts.User'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # Applied to every list endpoint: client-adjustable page size, capped (see store/pagination.py)
    'DEFAULT_PAGINATION_CLASS' : 'store.pagination.DefaultPagination',

    # Filtering, search and ordering are available on every view;
    # each view opts in by declaring filterset_class / search_fields / ordering_fields
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Rate limits: anonymous visitors are counted by IP, signed-in users by account.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],

    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        # Custom scope for the login view: low enough to stop password guessing.
        'login': '5/minute',
    },
}


SPECTACULAR_SETTINGS = {
    'TITLE': 'E-Commerce API',
    'DESCRIPTION': (
        'REST API for an e-commerce store: JWT authentication with token rotation, '
        'products and categories, reviews, a shopping cart, and orders with '
        'stock management and safe concurrent checkout.'
    ),
    'VERSION': '1.1.0',
    # Hide the raw schema endpoint from the docs page itself.
    'SERVE_INCLUDE_SCHEMA': False,
    # Show separate request/response shapes (e.g. product_id in, product out).
    'COMPONENT_SPLIT_REQUEST': True,

    # Pin ReDoc: the latest release breaks when loaded as a classic script.
    'REDOC_DIST': 'https://cdn.jsdelivr.net/npm/redoc@2.1.5',
}


# Short-lived access tokens limit the damage if one leaks; the refresh
# token keeps users logged in without asking for the password again.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Every refresh returns a new refresh token...
    'ROTATE_REFRESH_TOKENS': True,
    # ...and the old one stops working, so a stolen token can only be used once.
    'BLACKLIST_AFTER_ROTATION': True,

    'AUTH_HEADER_TYPES': ('Bearer',),
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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


# Internationalization and timezone configuration
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Officially supported languages in the store
LANGUAGES = [
    ('en', 'English'),
    ('ar', 'Arabic')
]

# Directory path where translation source files are located
LOCALE_PATHS = [
    BASE_DIR / 'locale',   
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
# collectstatic gathers every app's static files here, for whitenoise to serve
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}


# Configuration for user-uploaded files and product media
import os
MEDIA_URL = '/store/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'store', 'media')


STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    # Compressed files with a content hash in their names, so browsers can cache them safely
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}


# Production security: only when DEBUG is off
if not DEBUG:
    # Render handles HTTPS in front of Django and tells it through this header
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Cookies are only sent over HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Redirect http:// to https://. Turned on in production only, through the environment
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)