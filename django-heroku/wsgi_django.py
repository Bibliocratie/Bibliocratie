import os

if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django-heroku.settings.prod')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import newrelic.agent
application = newrelic.agent.WSGIApplicationWrapper(application)