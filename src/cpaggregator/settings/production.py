import os
import django_heroku

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS =  ['competitive.herokuapp.com']

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': django_heroku.dj_database_url.parse(os.environ.get('DATABASE_URL', ''))
}

# SSL Settings for Heroku.
CORS_REPLACE_HTTPS_REFERER = True
HOST_SCHEME = "https://"
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 1000000
SECURE_FRAME_DENY = True

# Activate Django-Heroku.
django_heroku.settings(locals())
