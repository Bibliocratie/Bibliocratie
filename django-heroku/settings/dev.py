# coding=utf-8
"""Development settings and globals."""

from os.path import join, normpath
import dotenv
import os
PROJECT_ROOT = os.path.dirname(os.path.normpath(os.path.join(__file__, '..', '..')))
dotenv.load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
from common import *


########## DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True

USE_S3 = False
try:
    if os.environ.get('USE_S3')=='True':
        USE_S3 = True
except:
    pass

DEBUG_TOOLBAR = True

########## END DEBUG CONFIGURATION

# Allow all host headers
ALLOWED_HOSTS = ['*']

########## LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'filters': {
#         'require_debug_false': {
#             '()': 'django.utils.log.RequireDebugFalse'
#             }
#         },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler'
#         },
#         'mail_admins': {
#             'level': 'ERROR',
#             'class': 'django.utils.log.AdminEmailHandler',
#             'email_backend' : EMAIL_BACKEND,
#             'include_html': True,
#         },
#         'file': {
#             'level': 'DEBUG',
#             'class': 'logging.FileHandler',
#             'filename': '/Users/Exlivris3/Devel/bibliocratie/debug.log',
#         },
#     },
#     'loggers': {
#         'django.request': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'sorl': {
#             'handlers': ['console'],
#             'level': 'INFO',
#             'propagate': True,
#         },
#         'celery': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'bibliocratie.tasks': {
#             'handlers': ['mail_admins'],
#             'level': 'ERROR',
#             'propagate': True,
#         },
#     }
# }
########## END LOGGING CONFIGURATION

CELERY_ALWAYS_EAGER = True

########## THUMBNAIL BACKEND
THUMBNAIL_BACKEND = 'sorl.thumbnail.base.ThumbnailBackend'
########## END THUMBNAIL BACKEND

########## EMAIL CONFIGURATION
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
########## END EMAIL CONFIGURATION


# ########## CACHE CONFIGURATION
# # See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
# ########## END CACHE CONFIGURATION

########## TOOLBAR CONFIGURATION
# See: https://github.com/django-debug-toolbar/django-debug-toolbar#installation

#La toolbar ne marche pas avec le S3
if not USE_S3 and DEBUG_TOOLBAR:
    INTERNAL_IPS = ('127.0.0.1','78.192.252.189')

    INSTALLED_APPS += (
        'debug_toolbar',
    )

    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    DEBUG_TOOLBAR_CONFIG = {
        'DISABLE_PANEL': set(['debug_toolbar.panels.redirects.RedirectsPanel']),
    }
########## END TOOLBAR CONFIGURATION

########## WebSocket CONFIGURATION
WSGI_APPLICATION = 'ws4redis.django_runserver.application'
########## End WebSocket CONFIGURATION

########## CELERY CONFIGURATION

CELERY_REDIRECT_STDOUTS_LEVEL=DEBUG

########## END CELERY CONFIGURATION

########## DEBUG TOOLBAR
def show_toolbar(request):
    return True
SHOW_TOOLBAR_CALLBACK = show_toolbar
########## END CELERY CONFIGURATION

########## COMPRESSION CONFIGURATION
# URL prefix for static files.

STATIC_URL = '/static/'
COMPRESS_ENABLED = False
COMPRESS_URL = STATIC_URL
COMPRESS_OFFLINE_CONTEXT = {'STATIC_URL': STATIC_URL,'csrf_token': "NOTPROVIDED"}

COMPRESS_OFFLINE = False

try:
    S3_URL = 'http://%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
except:
    print "AWS_STORAGE_BUCKET_NAME was not found in env"

COUNTRIES_FLAG_URL = '/static/drapeaux/{code}.gif'

if USE_S3:
    COMPRESS_OFFLINE = False
    STATICFILES_STORAGE = 'django-heroku.s3.CompressorS3BotoStorage'
    DEFAULT_FILE_STORAGE = 'django-heroku.s3.MediaS3BotoStorage'
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE
    MEDIA_URL = S3_URL + '/media/'
    # Add this line, if you're using ``django-compressor``
    COMPRESS_STORAGE = STATICFILES_STORAGE
    AWS_S3_SECURE_URLS = False
    STATIC_URL = S3_URL + '/compressor/'
    COMPRESS_URL = STATIC_URL
    FULL_DOMAIN = S3_URL
    COUNTRIES_FLAG_URL = COMPRESS_URL + 'drapeaux/{code}.gif'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

COMPRESS_TEMPLATE_FILTER_CONTEXT = {'static':STATIC_URL}
########## END COMPRESSION CONFIGURATION

# Set the session cookie domain
SESSION_COOKIE_DOMAIN = '.bibliocratie.dev'
CSRF_COOKIE_DOMAIN = '.bibliocratie.dev'

ROSETTA_UWSGI_AUTO_RELOAD = True
