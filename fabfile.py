# -*- coding: utf-8 -*-
from fabric.api import local
from fabric.api import settings
from fabric.contrib import django
import os

def fixture_prod():
    local('python manage.py loaddata fixture_site')
    local('python manage.py loaddata fixture_expedition')
    local('python manage.py loaddata fixture_fournisseurs')
    local('python manage.py loaddata fixture_urlindex_dev')

def fixture_dev():
    local('python manage.py loaddata fixture_site_dev')
    local('python manage.py loaddata fixture_expedition')
    local('python manage.py loaddata fixture_fournisseurs')
    local('python manage.py loaddata fixture_urlindex_dev')

#update des dependance python
def update():
    django.settings_module('django-heroku.settings.dev')
    local('pip-review --interactive')

def commit():
    print("enter your git commit comment: ")
    comment = raw_input()
    local('git add .')
    with settings(warn_only=True):
        local('git commit -m "%s"' % comment)
    local('git push -u origin master')


#Deploiement sur Heroku de la preprod
def deploy_prod():
    local('heroku maintenance:on --remote prod')
    local('git push prod gitprod:master')
    # local('heroku run fab herokubrew --size PX')  #plus rapide et plus cher
    local('heroku run python manage.py migrate --remote prod')
    local('heroku run fab herokubrew --remote prod')
    local('heroku restart --remote prod')
    local('heroku maintenance:off --remote prod')

#Deploiement sur Heroku de la preprod
def deploy_preprod():
    local('heroku maintenance:on --remote preprod')
    local('git push preprod gitpreprod:master')
    # local('heroku run fab herokubrew --size PX')  #plus rapide et plus cher
    local('heroku run python manage.py migrate --remote preprod')
    local('heroku run fab herokubrew --remote preprod')
    local('heroku restart --remote preprod')
    local('heroku maintenance:off --remote preprod')

#Procédure lancée sur le serveur apres le git push heroku
def herokubrew():
    local('python manage.py installwatson')
    local('python manage.py buildwatson')
    fixture_prod()
    local('bower install --config.interactive=false')
    local('python manage.py collectstatic --noinput')
    local('python manage.py compress')

#Procédure lancée sur le serveur apres le git push heroku
def herokuminibrew():
    local('bower install --config.interactive=false')
    local('python manage.py collectstatic --noinput')
    local('python manage.py compress')


#Deploiement des statics sur le S3 depuis le dev
def static():
    django.settings_module('django-heroku.settings.dev')
    os.environ['USE_S3']="True"
    local('./manage.py collectstatic --noinput')
    local('./manage.py compress --force')
    os.environ['USE_S3']="False"

#mise a jour des dependances bower en dev
def bower():
    os.environ['USE_S3']="False"
    django.settings_module('django-heroku.settings.dev')
    local('./manage.py bower install')

def dev():
    django.settings_module('django-heroku.settings.dev')
    local('pip install -r requirements.txt')
    local('python manage.py migrate')
    local('bower install')
    local('python manage.py buildwatson')

def batch():
    django.settings_module('django-heroku.settings.dev')
    local('python manage.py batch batch_passage_en_presouscription')
    local('python manage.py batch batch_fin_presouscription')
    local('python manage.py batch batch_souscription')
    local('python manage.py batch batch_fin_campagne')
    local('python manage.py batch batch_task_mail_auteur_demandes_new_souscription')
    local('python manage.py batch batch_detecte_nouveaux_livres')


def installdev():
    django.settings_module('django-heroku.settings.dev')
    local('pip install -r requirements.txt')
    local('python manage.py migrate')
    local('python manage.py installwatson')
    local('python manage.py buildwatson')
    # fixture_dev()
    local('bower install --config.interactive=false')


#a lancer avec une installe fraiche.
def celery():
    local('celery -A django-heroku worker -B -l info -P threads')
