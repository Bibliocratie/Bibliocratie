from __future__ import absolute_import

__author__ = 'bibliocratie'

import os


# import dotenv
# PROJECT_ROOT = os.path.dirname(os.path.normpath(os.path.join(__file__, '..')))
# dotenv.load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# set the default Django settings module for the 'celery' program.
if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django-heroku.settings.prod')

from celery import Celery
from django.conf import settings

app = Celery('apps.bibliocratie')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))