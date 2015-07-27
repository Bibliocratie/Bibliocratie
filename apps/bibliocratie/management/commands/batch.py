# -*- coding: utf-8 -*-
__author__ = 'Exlivris3'

from django.core.management.base import BaseCommand, CommandError
from bibliocratie.tasks import *


class Command(BaseCommand):
    help = 'Executer un batch'
    missing_args_message = '\nNom du batch non reconnu. Syntaxe ./manage.py batch <batchname> -date <date>. Batchs disponibles : \nbatch_passage_en_presouscription \nbatch_fin_presouscription \nbatch_souscription ' + \
            '\nbatch_fin_campagne \nbatch_me_rappeler \nbatch_mail_auteur_demandes_new_souscription \nbatch_detecte_nouveaux_livres '

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('name', nargs='+', type=unicode)

        # Named (optional) arguments
        parser.add_argument('-date', default=None, help='Forcer la date de passage du batch', type=unicode)

    def handle(self, *args, **options):
        batch_name = options['name'].pop()
        date=None
        if options['date']:
            date = options['date']
        if batch_name=="batch_passage_en_presouscription":
            batch_passage_en_presouscription.delay(date)
        elif batch_name=="batch_fin_presouscription":
            batch_fin_presouscription.delay(date)
        elif batch_name=="batch_souscription":
            batch_souscription.delay(date)
        elif batch_name=="batch_fin_campagne":
            batch_fin_campagne.delay(date)
        elif batch_name=="batch_me_rappeler":
            batch_me_rappeler.delay(date)
        elif batch_name=="batch_mail_auteur_demandes_new_souscription":
            batch_mail_auteur_demandes_new_souscription.delay(date)
        elif batch_name=='batch_jour5':
            batch_jour5.delay(date)
        elif batch_name=='batch_jour20':
            batch_jour20.delay(date)
        elif batch_name=='batch_jour30':
            batch_jour30.delay(date)
        elif batch_name=='batch_jour40':
            batch_jour40.delay(date)
        elif batch_name=='batch_5_to_end':
            batch_5_to_end.delay(date)
        elif batch_name=='batch_souscription85':
            batch_souscription85.delay(date)
        elif batch_name=='batch_souscription100':
            batch_souscription100.delay(date)
        elif batch_name=='batch_souscription200':
            batch_souscription200.delay(date)
        elif batch_name=='all':
            batch_passage_en_presouscription.delay(date)
            batch_fin_presouscription.delay(date)
            batch_souscription.delay(date)
            batch_fin_campagne.delay(date)
            batch_me_rappeler.delay(date)
            batch_mail_auteur_demandes_new_souscription.delay(date)
            batch_jour5.delay(date)
            batch_jour20.delay(date)
            batch_jour30.delay(date)
            batch_jour40.delay(date)
            batch_5_to_end.delay(date)
            batch_souscription85.delay(date)
            batch_souscription100.delay(date)
            batch_souscription200.delay(date)
        else:
            message = 'La commande "%s" est inconnue. ' % batch_name
            raise CommandError(message)
