#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django-heroku.settings.dev')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
