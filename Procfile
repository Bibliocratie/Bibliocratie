web: newrelic-admin run-program uwsgi --ini $UWSGI_INI_FILE
worker: newrelic-admin run-program celery -A django-heroku worker -l info -B