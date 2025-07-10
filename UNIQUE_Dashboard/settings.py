import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

load_dotenv()  # for Railway or .env use

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 SECURITY WARNING: Don't hardcode secret keys in production!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'unsafe-secret-key-for-dev')

DEBUG = True
# DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Railway automatically injects your app domain in production.
# ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# ✅ Applications
INSTALLED_APPS = [
    'dashboard',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

# ✅ Middleware stack
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # for static file serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'UNIQUE_Dashboard.urls'

# ✅ Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'dashboard/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.branch_list',
                'dashboard.context_processors.user_role',
                'dashboard.context_processors.sidebar_context',
                'dashboard.context_processors.recent_updates',
                'dashboard.context_processors.sales_analytics',
            ],
        },
    },
]

WSGI_APPLICATION = 'UNIQUE_Dashboard.wsgi.application'

# ✅ Database config (Railway injects DATABASE_URL automatically)
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# ✅ Password validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ✅ Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'  # change if needed
USE_I18N = True
USE_TZ = True

# ✅ Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'dashboard/static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # for collectstatic
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ✅ Media files
MEDIA_URL = '/memos/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'memos')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ✅ CSRF / COOKIE settings for production
CSRF_TRUSTED_ORIGINS = [
    'https://uniquedashboard.up.railway.app/',
    'https://*.railway.app',
    'http://localhost',
    'http://127.0.0.1',
]

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

ALLOWED_HOSTS = ['*']


# ✅ WhatsApp / Twilio (optional)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
