# -*- coding: utf-8 -*-
"""Common settings and globals."""

from sys import path
import os
from urlparse import urlparse
import dj_redis_url
from datetime import timedelta
from celery.schedules import crontab
from datetime import datetime

########## PATH CONFIGURATION
SETTINGS_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, os.pardir, os.pardir))
APPS_ROOT = os.path.join(PROJECT_DIR, 'apps')
DJANGO_PROJECT = os.path.basename(PROJECT_DIR.rstrip('/'))
# Add app folder  to our pythonpath,
path.append(APPS_ROOT)
# path.append(os.path.join(PROJECT_DIR, 'django-countries'))
ALLOWED_INCLUDE_ROOTS = (PROJECT_DIR,)
########## END PATH CONFIGURATION

########## DATABASE CONFIGURATION
# Parse database configuration from $DATABASE_URL
import dj_database_url
DATABASES = {
    'default': dj_database_url.config()
}
########## END DATABASE CONFIGURATION

########## SECURITY################
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_CONTENT_TYPE_NOSNIFF=True
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
CSRF_COOKIE_HTTPONLY=False
X_FRAME_OPTIONS='DENY'
########## SECURITY################

########## CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
#CACHES = memcacheify()
try:
    REDISCLOUD_URL = os.environ['REDISCLOUD_URL']
except:
    REDISCLOUD_URL = os.environ['REDIS_URL']

try:
    redis_url = urlparse(REDISCLOUD_URL)
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': '%s:%s' % (redis_url.hostname, redis_url.port),
            'TIMEOUT': 60,
            'OPTIONS': {
                'PASSWORD': redis_url.password,
                'DB': 0,
            }
        }
    }
except:
    print "REDISCLOUD_URL could not be parsed"

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600
CACHE_MIDDLEWARE_KEY_PREFIX  = "biblio-"
########## END CACHE CONFIGURATION

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


######### Time Zone configuration
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# If you set this to False, Django will not use timezone-aware datetimes.
# pytz is in requirements.txt because it's "highly recommended" when using
# timezone support.
# https://docs.djangoproject.com/en/1.4/topics/i18n/timezones/
USE_TZ = True

######### END Time Zone configuration


########## LANGAGE CONFIGURATION
from django.utils.translation import ugettext_lazy as _

LANGUAGES = (
    ('fr', _('French')),
    ('en', _('English')),
)
# default language, it will be used, if django can't recognize user's language
LANGUAGE_CODE = 'fr'

# enable django’s translation system
USE_I18N = True

# specify path for translation files
# First one is for apps the second for the main templates
# LOCALE_PATHS = ( '../locale', os.path.join(PROJECT_DIR, 'locale'),)
LOCALE_PATHS = ( os.path.join(PROJECT_DIR, 'apps/bibliocratie/locale'),)

########## END LANGAGE CONFIGURATION

########## REDACTOR CONFIGURATION
REDACTOR_OPTIONS = {'lang':'fr', 'buttons': ['bold', 'italic', 'deleted', 'unorderedlist', 'orderedlist', 'outdent', 'indent', 'image', 'file', 'link', 'alignment', 'horizontalrule']}
REDACTOR_UPLOAD = 'uploads/'
REDACTOR_UPLOAD_HANDLER = 'redactor.handlers.DateDirectoryUploader'
REDACTOR_AUTH_DECORATOR = 'django.contrib.auth.decorators.login_required'
########## END REDACTOR CONFIGURATION


########## DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = False
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
########## END DEBUG CONFIGURATION


########## MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ('admin', 'admin@example.com'),
)

BATCH_EMAIL = (
    ('staff', 'staff@example.com'),
)


# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
########## END MANAGER CONFIGURATION

########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# EMAIL_BACKEND = 'postmark.backends.PostmarkBackend'
EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'

DEFAULT_FROM_EMAIL = 'contact@example.com'

POSTMARK_API_KEY     = 'postmark_api_key'
POSTMARK_TEST_MODE   = False
POSTMARK_TRACK_OPENS = False
########## END EMAIL CONFIGURATION


########## GENERAL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = 'Europe/Paris'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'fr'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

########## END GENERAL CONFIGURATION


########## MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'static', 'media')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'
########## END MEDIA CONFIGURATION


########## STATIC FILE CONFIGURATION
# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.comstatic/"
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static', 'assets')

#Files in this folder will be uploaded to S3, but not in github
UPLOAD_STATIC_ROOT = os.path.join(PROJECT_DIR, 'static', 'uploadstatic')

STATICFILES_DIRS = (
    UPLOAD_STATIC_ROOT,
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'nodebow.finders.BowerComponentsFinder',
    'compressor.finders.CompressorFinder',
)
########## END STATIC FILE CONFIGURATION


########## COMPRESSION CONFIGURATION
COMPRESS_ENABLED = True
COMPRESS_PARSER = 'compressor.parser.HtmlParser'

COMPRESS_ROOT = STATIC_ROOT

# See: http://django_compressor.readthedocs.org/en/latest/settings/#django.conf.settings.COMPRESS_CSS_FILTERS
# settings.py
COMPRESS_CSS_FILTERS = [
    'compressor.filters.template.TemplateFilter',
    'django-heroku.compress_filters.CustomCssAbsoluteFilter',
    # 'compressor.filters.cssmin.CSSMinFilter',
]

# See: http://django_compressor.readthedocs.org/en/latest/settings/#django.conf.settings.COMPRESS_JS_FILTERS
COMPRESS_JS_FILTERS = [
     'compressor.filters.jsmin.JSMinFilter',
]
########## END COMPRESSION CONFIGURATION

########## FIXTURE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = [
    os.path.join(DJANGO_PROJECT, 'fixtures')
]
########## END FIXTURE CONFIGURATION


########## TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
TEMPLATE_LOADERS = (
    'django.template.loaders.cached.Loader'
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs

TEMPLATE_DIRS = (os.path.join(PROJECT_DIR, 'bibliocratie','templates'),)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.core.context_processors.debug',
                'django.core.context_processors.i18n',
                'django.core.context_processors.media',
                'django.core.context_processors.static',
                'django.core.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'ws4redis.context_processors.default',
                'apps.bibliocratie.context_processors.login',
                'apps.bibliocratie.context_processors.panier',
                'apps.bibliocratie.context_processors.contact_form',
                'apps.bibliocratie.context_processors.redactor_upload_dir',
                'apps.bibliocratie.context_processors.facebook_app_id',

                # `allauth` needs this from django
                'django.core.context_processors.request',

                # `allauth` specific context processors
                'allauth.account.context_processors.account',
                'allauth.socialaccount.context_processors.socialaccount',
            ],
            'debug':DEBUG,
        },
    },
]

location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

########## END TEMPLATE CONFIGURATION


########## SESSION CONFIGURATION
SESSION_ENGINE = 'redis_sessions_fork.session'

try:
    SESSION_REDIS_URL = os.environ.get('REDISCLOUD_URL')
    CAPITAL_WS4REDIS_CONNECTION = dj_redis_url.parse(SESSION_REDIS_URL)
    SESSION_REDIS_HOST = CAPITAL_WS4REDIS_CONNECTION['HOST']
    SESSION_REDIS_PORT = CAPITAL_WS4REDIS_CONNECTION['PORT']
    SESSION_REDIS_DB = CAPITAL_WS4REDIS_CONNECTION['DB']
    SESSION_REDIS_PASSWORD = CAPITAL_WS4REDIS_CONNECTION['PASSWORD']
except:
    print "REDISCLOUD_URL was not found in env"

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

SESSION_SAVE_EVERY_REQUEST = True

SESSION_IDLE_TIMEOUT = 30000

WS4REDIS_EXPIRE=0

# CSRF_COOKIE_NAME = 'csrftoken'
########## END SESSION CONFIGURATION


########## MIDDLEWARE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#middleware-classes
MIDDLEWARE_CLASSES = (
    'djangular.middleware.DjangularUrlMiddleware',
    # Cache
    'django.middleware.cache.UpdateCacheMiddleware',
    # Use GZip compression to reduce bandwidth.
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Default Django middleware.
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'user_sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'watson.middleware.SearchContextMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Cache
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'bibliocratie.middleware.SessionIdleTimeout',
)
########## END MIDDLEWARE CONFIGURATION

########## AUTHENTICATION BACKENDS
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

ANONYMOUS_USER_ID = -1
LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'
########## END AUTHENTICATION BACKENDS

########## URL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'django-heroku.urls'
########## END URL CONFIGURATION

########## Append slash
APPEND_SLASH = True
########## End Append slash

########## APP CONFIGURATION
DJANGO_APPS = [
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'user_sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Useful template tags:
    'django.contrib.humanize',
]


THIRD_PARTY_APPS = [
    # Static file management:
    'compressor',

    #front package manager
    'nodebow',

    #redis sessions management
    'redis_sessions_fork',

    #Thumbnail
    'sorl.thumbnail',

    #rest framework
    'rest_framework',
    'rest_framework.authtoken',

    #postmark
    'postmark',

    #S3
    'storages',

    #websocket for redis
    'ws4redis',

    #django angular
    'djangular',

    #country field
    'django_countries',
    #admin
    'nested_inline',
    #mega search
    'watson',
    #redactorfield
    'redactor',
    #tradution
    'rosetta',
    #rest authentification
    'rest_auth',

    #authentification email
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
]

LOCAL_APPS = [
    'django-heroku',
    'apps.bibliocratie',
    # 'etherpadlite',
]

ADMIN_APPS = [
    # Admin panel and documentation:
    'django.contrib.admin',
    'django.contrib.admindocs',
]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS + ADMIN_APPS

########## END APP CONFIGURATION


########## AUTH CONFIGURATION
REST_SESSION_LOGIN = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_USERNAME_BLACKLIST = []
AUTH_USER_MODEL = "bibliocratie.BiblioUser"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
########## END AUTH CONFIGURATION

########## django-websocket-redis CONFIGURATION
WEBSOCKET_URL = '/ws/'
WS4REDIS_PREFIX = 'ws'
try:
    REDISCLOUD_URL = os.environ['REDISCLOUD_URL']
    CAPITAL_WS4REDIS_CONNECTION = dj_redis_url.parse(REDISCLOUD_URL)
    WS4REDIS_CONNECTION = {
        'host': CAPITAL_WS4REDIS_CONNECTION['HOST'],
        'port': CAPITAL_WS4REDIS_CONNECTION['PORT'],
        'db': CAPITAL_WS4REDIS_CONNECTION['DB'],
        'password': CAPITAL_WS4REDIS_CONNECTION['PASSWORD'],
    }

except:
    print "DJANGO WEBSOCKET REDIS ERROR : REDISCLOUD_URL was not found in env"

########## END django-websocket-redis CONFIGURATION

######### sorl.thumbnail ########
THUMBNAIL_DEBUG = False
DJANGORESIZED_DEFAULT_SIZE = [1920, 1080]
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_KEY_PREFIX = "sorl-thumbnail:"
try:
    REDISCLOUD_URL = os.environ['REDISCLOUD_URL']
    CAPITAL_WS4REDIS_CONNECTION = dj_redis_url.parse(REDISCLOUD_URL)
    THUMBNAIL_REDIS_HOST = CAPITAL_WS4REDIS_CONNECTION['HOST']
    THUMBNAIL_REDIS_PORT = CAPITAL_WS4REDIS_CONNECTION['PORT']
    THUMBNAIL_REDIS_DB = CAPITAL_WS4REDIS_CONNECTION['DB']
    THUMBNAIL_REDIS_PASSWORD = CAPITAL_WS4REDIS_CONNECTION['PASSWORD']
except:
    print "SORL THUMBNAIL ERROR : REDISCLOUD_URL was not found in env"
######### END sorl.thumbnail ########

########## LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
    'require_debug_false': {
        '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}
########## END LOGGING CONFIGURATION


########## WSGI CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'bibliocratie.wsgi_django.application'
########## END WSGI CONFIGURATION


########## REST_FRAMEWORK CONFIGURATION
REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    )
}
########## END REST_FRAMEWORK CONFIGURATION


########## CELERY CONFIGURATION
BROKER_POOL_LIMIT = 10
CELERY_RESULT_BACKEND=REDISCLOUD_URL
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'

try:
    BROKER_URL = os.environ['REDISCLOUD_URL']
except:
    print "REDISCLOUD_URL was not found in env"

CELERY_TIMEZONE = 'Europe/Paris'

CELERYBEAT_SCHEDULE = {
    'batch_passage_en_presouscription': {
        'task': 'batch_passage_en_presouscription',
        'schedule': crontab(hour=8, minute=00, day_of_week='wed'), #mercredi a 08h00
    },

    'batch_fin_presouscription': {
        'task': 'batch_fin_presouscription',
        'schedule': crontab(hour=0, minute=01, day_of_week='mon'), #lundi a 0h01
    },

    'batch_souscription': {
        'task': 'batch_souscription',
        'schedule': crontab(hour=8, minute=00, day_of_week='wed'), #mercredi a 08h00
    },

    'batch_fin_campagne': {
        'task': 'batch_fin_campagne',
        'schedule': crontab(hour=0, minute=01, day_of_week='sun'), #dimanche a 0h01
    },

    # 5 jours après la souscription, si il y a moins de 4 ventes on envoie un mail a l'auteur
    'batch_jour5': {
        'task': 'batch_jour5',
        'schedule': crontab(hour=10, minute=00, day_of_week='mon'), #lundi a 10:00
    },

    # 20 jours après la souscription, si il y a moins de 20 ventes on envoie un mail a l'auteur
    'batch_jour20': {
        'task': 'batch_jour20',
        'schedule': crontab(hour=10, minute=00, day_of_week='tue'), # mardi a 10h00
    },

    # 30 jours après la souscription, on envoie un mail a l'auteur
    'batch_jour30': {
        'task': 'batch_jour30',
        'schedule': crontab(hour=10, minute=00, day_of_week='fri'), #vendredi a 10h00
    },

    # 5 jours avant la fin de souscription, on envoie un mail a l'auteur si les ventes dépassent 50%
    'batch_5_to_end': {
        'task': 'batch_5_to_end',
        'schedule': crontab(hour=10, minute=00, day_of_week='mon'), # lundi a 10h00
    },

    # batch envoyé 40 jours après la fermeture de la souscription. Mail envoyé a l'auteur pour retour de lecture
    'batch_jour40_afer_closed': {
        'task': 'batch_jour40_afer_closed',
        'schedule': crontab(hour=10, minute=00, day_of_week='fri'), # vendredi a 10h00
    },

    # batch qui detecte les livres qui ont passé 85%
    'batch_souscription85': {
        'task': 'batch_souscription85',
        'schedule': crontab(hour=10, minute=00, day_of_week='mon-sun'), # tous les jours a 10h00
    },

    # batch qui detecte les livres qui ont passé 100%
    'batch_souscription100': {
        'task': 'batch_souscription100',
        'schedule': crontab(hour=10, minute=00, day_of_week='mon-sun'), # tous les jours a 10h00
    },

    # batch qui detecte les livres qui ont passé 200%
    'batch_souscription200': {
        'task': 'batch_souscription200',
        'schedule': crontab(hour=10, minute=00, day_of_week='mon-sun'), # tous les jours a 10h00
    },

    # batch mail envoyé aux clients qui se sont inscrits 2 jours avant la fin de souscription,
    'batch_me_rappeler': {
        'task': 'batch_me_rappeler',
        'schedule': crontab(hour=10, minute=00, day_of_week='fri'), # vendredi a 10h00
    },

    #batch mail envoyés aux auteurs dont le livre a fait l'objet de demandes de resouscription
    'batch_mail_auteur_demandes_new_souscription': {
        'task': 'batch_mail_auteur_demandes_new_souscription',
        'schedule': crontab(hour=10, minute=00, day_of_week='mon-sun'), # tous les jours a 10h00
    },
}

########## END CELERY CONFIGURATION

########## STORAGE CONFIGURATION

# See: http://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html#settings
try:
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
except:
    print "AWS_STORAGE_BUCKET_NAME was not found in env"

try:
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
except:
    print "AWS_ACCESS_KEY_ID was not found in env"

try:
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
except:
    print "AWS_SECRET_ACCESS_KEY was not found in env"

try:
    S3_URL = 'http://%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
except:
    print "AWS_STORAGE_BUCKET_NAME not defined"

AWS_AUTO_CREATE_BUCKET = True
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = True

# AWS cache settings, don't change unless you know what you're doing:
AWS_EXPIRY = 60 * 60 * 24 * 7
AWS_HEADERS = {
    'Cache-Control': 'max-age=%d, s-maxage=%d, must-revalidate' % (AWS_EXPIRY,
        AWS_EXPIRY)
}
########## END STORAGE CONFIGURATION


########## PAYLINE CONFIGURATION
try:
    PAYLINE_ACCESS_KEY = os.environ['PAYLINE_ACCESS_KEY']
except:
    print "PAYLINE_ACCESS_KEY was not found in env"

try:
    PAYLINE_MERCHANT_ID = os.environ['PAYLINE_MERCHANT_ID']
except:
    print "PAYLINE_MERCHANT_ID was not found in env"

try:
    PAYLINE_CONTRACT_NUMBER = os.environ['PAYLINE_CONTRACT_NUMBER']
except:
    print "PAYLINE_CONTRACT_NUMBER was not found in env"

try:
    PAYLINE_URL = os.environ['PAYLINE_URL']
except:
    print "PAYLINE_URL was not found in env"
########## END PAYLINE CONFIGURATION


########## ETHERPAD CONFIGURATION
# try:
#     ETHERPAD_API_KEY = os.environ['ETHERPAD_API_KEY']
# except:
#     print "ETHERPAD_API_KEY was not found in env"
#
# try:
#     ETHERPAD_API_URL = os.environ['ETHERPAD_API_URL']
# except:
#     print "ETHERPAD_API_URL was not found in env"

#SESSION_COOKIE_NAME = 'sessionID'

########## END ETHERPAD CONFIGURATION

########## GOOGLE WORKSHEET CONFIGURATION
try:
    GOOGLE_ACCOUNT = os.environ['GOOGLE_ACCOUNT']
except:
    print "GOOGLE_ACCOUNT was not found in env"

try:
    GOOGLE_PASSWORD = os.environ['GOOGLE_PASSWORD']
except:
    print "GOOGLE_PASSWORD was not found in env"

########## END GOOGLE WORKSHEET CONFIGURATION

########## FACEBOOK CONFIGURATION
FACEBOOK_APP_ID = os.environ['FACEBOOK_APP_ID']
FACEBOOK_SECRET = os.environ['FACEBOOK_SECRET']
########## END FACEBOOK CONFIGURATION

##########SEUIL DE PASSAGE DU BATCH D'ENVOI DE MAILS AUX AUTEURS
SEUIL_DEMANDES_RESOUSCRIPTION = 20
NB_JOURS_NOUVEAU_LIVRE = 7
FIRST_COMMANDE_NUMBER = 30000
TIMELINE_ELEMENTS_BEGORE_SUGGESTION = 5

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
    'hashers_passlib.phpass',
)
