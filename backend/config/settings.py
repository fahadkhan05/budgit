"""
Django Settings
===============
This file is the "control panel" for your entire backend application.
Every major behavior — database, authentication, installed apps, CORS — is
configured here.

LEARNING CONCEPTS IN THIS FILE:
  1. INSTALLED_APPS   — How Django knows which modules are active
  2. MIDDLEWARE        — A pipeline that processes every request & response
  3. DATABASES         — Where data is stored (SQLite here, PostgreSQL in prod)
  4. REST_FRAMEWORK    — Global config for the API (auth classes, permissions)
  5. SIMPLE_JWT        — Settings for JWT-based authentication
  6. CORS              — Allowing the React frontend to talk to this backend
"""

import os
import dj_database_url
from pathlib import Path
from datetime import timedelta

# BASE_DIR points to the 'backend/' folder.
# Path(__file__) = this file; .resolve().parent.parent = two levels up
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------------
# In production, SECRET_KEY and DEBUG come from environment variables set in
# Railway's dashboard. Locally they fall back to safe dev defaults.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-budget-tracker-dev-key-change-in-prod')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS_EXTRA lets you add your Railway domain via env var.
# Example: ALLOWED_HOSTS_EXTRA=budgit-backend.up.railway.app
_extra_hosts = [h.strip() for h in os.environ.get('ALLOWED_HOSTS_EXTRA', '').split(',') if h.strip()]
ALLOWED_HOSTS = ['localhost', '127.0.0.1'] + _extra_hosts

# ---------------------------------------------------------------------------
# INSTALLED APPS
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # OUR custom apps
    'users',
    'budgets',
    'transactions',
    'recommendations',
    'plaid_integration',
]

# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------
# WhiteNoise (after SecurityMiddleware) lets Django serve its own static files
# in production without needing a separate file server like nginx.
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # Must be first!
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',      # Serve static files in prod
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
# If DATABASE_URL is set (Railway injects this automatically when you add a
# PostgreSQL plugin), use that. Otherwise fall back to SQLite for local dev.
_database_url = os.environ.get('DATABASE_URL')
if _database_url:
    DATABASES = {'default': dj_database_url.parse(_database_url, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------------------------------------------------------------
# CUSTOM USER MODEL
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# DJANGO REST FRAMEWORK
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# ---------------------------------------------------------------------------
# JWT SETTINGS
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'UPDATE_LAST_LOGIN': True,
}

# ---------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing)
# ---------------------------------------------------------------------------
# CORS_ALLOWED_ORIGINS_EXTRA lets you add your Vercel frontend URL via env var.
# Example: CORS_ALLOWED_ORIGINS_EXTRA=https://budgit.vercel.app
_extra_origins = [o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS_EXTRA', '').split(',') if o.strip()]
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
] + _extra_origins

# Allow all origins if CORS_ALLOW_ALL=True is set (useful for debugging)
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL', 'False') == 'True'
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# WhiteNoise compresses and caches static files automatically
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# PLAID CONFIGURATION
# ---------------------------------------------------------------------------
# Set these as environment variables (locally via export, in prod via Railway dashboard).
PLAID_CLIENT_ID = os.environ.get('PLAID_CLIENT_ID', '')
PLAID_SECRET    = os.environ.get('PLAID_SECRET', '')
PLAID_ENV       = os.environ.get('PLAID_ENV', 'sandbox')
