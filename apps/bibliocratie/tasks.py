# -*- coding: utf-8 -*-
from __future__ import absolute_import
from celery import shared_task
import  pytz
from django.utils import timezone
from django.db.models import F
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
from dateutil import parser
from django.utils.translation import ugettext as _
from rest_framework.renderers import JSONRenderer
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.db.models import Q, Count
from bibliocratie.models import Livre, Follow, Proposition, Souscription, BiblioUser, MeRappeler, Notification, Timeline, Commentaire
from bibliocratie.serializers import PanierApiSerializer, SouscriptionApiSerializer, NotificationApiSerializer, TimelineApiSerializer, LivreApiSerializer

from celery.utils.log import get_task_logger
import logging

logger = get_task_logger(__name__)

###########################BATCHS Bibliocratie####################################

def check_date(date, nom_batch):
    """prend une date en paramètre et la converti dans le bon timezone.
    S'il n'y a pas de date, prend la date actuelle
    """

    if date:
        naive = parser.parse(date)
        local = pytz.timezone("Europe/Paris")
        local_dt = local.localize(naive)
        logger.info('BATCH BIBLIOCRATIE {0} : date de passage : {1}'.format(nom_batch, local_dt))
        return local_dt

    else:
        local_dt = timezone.now()
        logger.info('BATCH BIBLIOCRATIE {0} : pas de date indiquee. Utilisation de la date serveur {1}'.format(nom_batch, local_dt))
        return local_dt

@shared_task(name='send_mail_auteur')
def send_mail_auteur(auteur, livre, template, sujet, souscription=None, souscripteur=None, user=None):
    """Envoi un mail à l'auteur"""
    if not auteur.is_active:
        logger.warning(auteur.email + ' est inactif')
        return
    ctx = {
        'user' : user,
        'souscripteur' : souscripteur,
        'souscription' : souscription,
        'auteur' : auteur,
        'livre' : livre
    }
    sujet = sujet
    to = [auteur.email]
    message = get_template('mails/' + template).render(Context(ctx))
    msg = EmailMessage(sujet, message, to=to)
    msg.content_subtype = 'html'
    msg.send()
    logger.info('mail ' + template + ' envoye a ' + auteur.email)

@shared_task(name='send_mail_with_context')
def send_mail_with_context(destinataire, ctx, template, sujet):
    """Envoi un mail avec un contexte passé en paramètre"""
    to = [destinataire]
    message = get_template('mails/' + template).render(Context(ctx))
    msg = EmailMessage(sujet, message, to=to)
    msg.content_subtype = 'html'
    msg.send()
    logger.info('mail ' + template + ' envoye a ' + destinataire)


@shared_task(name='batch_passage_en_presouscription')
def batch_passage_en_presouscription(date_de_passage=None):
    """Passe les livres en présouscription quand la date de début de la
    présouscrition est dépassé"""
    local_dt = check_date(date_de_passage, 'batch_passage_en_presouscription')
    if not local_dt:
        return

    livres = Livre.objects.filter(date_feedback__lte=local_dt).filter(pre_souscription=True).filter(phase='VALIDATE', is_active=True)
    logger.setLevel(logging.DEBUG)
    logger.info('BATCH BIBLIOCRATIE passage_en_presouscription : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        logger.info('BATCH BIBLIOCRATIE passage_en_presouscription : Traitement du livre {0}'.format(livre.titre.encode('utf-8')))
        auteurs = list()
        livre.phase = 'FEEDBACK'
        livre.save()
        for auteur in livre.auteurs.all():
            if not auteur.is_active:
                logger.warning(auteur.email + ' est inactif')
                continue
            auteurs.append(auteur)
            send_mail_auteur.delay(auteur, livre, 'presouscription_auteur.html', u'Votre présouscription est à présent active !')

@shared_task(name="batch_fin_presouscription")
def batch_fin_presouscription(date_de_passage=None):
    """Passe les livres en présouscription en phase CREA FEE quand la date
    de fin de la présouscription est passée"""
    local_dt = check_date(date_de_passage, 'batch_fin_presouscription')
    if not local_dt:
        return

    livres = Livre.objects.filter(date_fin_presouscription__lte=local_dt).filter(phase="FEEDBACK", is_active=True)
    logger.info('BATCH BIBLIOCRATIE fin_presouscription : {0} livres à traiter'.format(livres.count()))
    for livre in livres:
        logger.info('BATCH BIBLIOCRATIE fin_presouscription : Traitement du livre {0}'.format(livre.titre.encode('utf-8')))
        livre.phase = 'CREA-FEE'
        livre.save()
        votes = livre.get_nb_votes() + livre._get_nb_propositions()
        for auteur in livre.auteurs.filter(is_active=True):
            ctx = {
                'auteur' : auteur,
                'livre' : livre,
                'nb_votes': votes
            }
            send_mail_with_context.delay(auteur.email, ctx, 'fin_presouscription.html', u'J-2 pour finaliser votre page de souscription')


@shared_task(name='batch_souscription')
def batch_souscription(date_de_passage=None):
    """Passe les livres en souscriptions quand la date de début de
    souscription est passé"""
    local_dt = check_date(date_de_passage, 'souscription')
    if not local_dt:
        return

    livres = Livre.objects.filter(date_souscription__lte=local_dt, is_active=True).filter(Q(phase='VAL-FEED') | Q(phase='VALIDATE',pre_souscription=False))
    logger.info('BATCH BIBLIOCRATIE souscription : {0} livres à traiter'.format(livres.count()))
    for livre in livres:
        logger.info('BATCH BIBLIOCRATIE souscription : Traitement du livre {0}'.format(livre.titre.encode('utf-8')))
        livre.phase = 'GETMONEY'
        livre.save()
        for auteur in livre.auteurs.all():
            send_mail_auteur.delay(auteur, livre, 'souscription_auteur.html', u'Votre souscription est à présent active !')
    task_detecte_vieux_livres.delay()


@shared_task(name='batch_fin_campagne')
def batch_fin_campagne(date_de_passage=None):

    """Passe les livres et les souscriptions liées en succès ou echec
    une fois la souscription terminée """
    local_dt = check_date(date_de_passage, 'batch_fin_campagne')
    if not local_dt:
        return

    livres = Livre.objects.filter(phase='GETMONEY', is_active=True)
    logger.info('BATCH BIBLIOCRATIE fin_campagne : {0} livres à traiter'.format(livres.count()))
    for livre in livres:
        date_fin = livre.date_souscription + timedelta(days=livre.nb_jours_campagne)
        if date_fin > local_dt:
            continue
        logger.info('BATCH BIBLIOCRATIE fin_campagne : Traitement du livre {0}'.format(livre.titre.encode('utf-8')))
        auteurs = list()
        souscriptions = Souscription.objects.filter(livre=livre)
        souscripteurs = list()
        for auteur in livre.auteurs.all():
            auteurs.append(auteur)
        for souscription in souscriptions:
            souscripteurs.append(souscription.panier.client)
        # REUSSI
        if livre._nb_exemplaires_souscrits() >= livre.nb_exemplaires_cible:
            livre.phase = 'SUCCES'
            for souscription in souscriptions:
                souscription.etat = 'SUC'
                souscription.save()
            for auteur in auteurs:
                send_mail_auteur.delay(auteur, livre, 'souscription_reussi_auteur.html', u'Félicitations !')
            for souscripteur in souscripteurs:
                if souscripteur not in auteurs:
                    if not souscripteur.is_active:
                        logger.warning(souscripteur.email + ' est inactif')
                        continue
                    ctx = {
                        'livre' : livre,
                        'souscripteur': souscripteur,
                        'date_butoire': livre.date_souscription + timedelta(days=livre.nb_jours_campagne) + timedelta(days=30),
                        'date_closed' : livre.date_souscription + timedelta(days=livre.nb_jours_campagne)
                    }
                    send_mail_with_context.delay(souscripteur.email, ctx, 'souscription_reussi_souscripteur.html', unicode(livre.titre) + u' // Succès de la souscription')
        # ECHEC
        else:
            livre.phase = 'ECHEC'
            for souscription in souscriptions:
                souscription.etat = 'ECH'
                souscription.save()
            for auteur in auteurs:
                send_mail_auteur.delay(auteur, livre, 'souscription_echec_auteur.html', 'Hélas...')
            for souscripteur in souscripteurs:
                if souscripteur not in auteurs:
                    send_mail_with_context.delay(souscripteur.email, {'livre': livre}, 'souscription_echec_souscripteur.html', unicode(livre.titre) + u' // Echec de la souscription')
        livre.date_closed = local_dt
        livre.save()


@shared_task(name='batch_jour5')
def batch_jour5(date_de_passage=None):
    """Si le livre a moins de 4 souscriptions après 5 jours de campagne,
    un mail est envoyé à l'auteur pour lui donner des conseils"""
    local_dt = check_date(date_de_passage, 'batch_jour5')
    if not local_dt:
        return
    livres = Livre.objects.filter(phase='GETMONEY', is_active=True, date_souscription__lte=date.today()-timedelta(days=5), jour5=None)
    logger.info('BATCH BIBLIOCRATIE batch_jour5 : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        if livre.nb_exemplaires_souscrits<=4:
            for auteur in livre.auteurs.all():
                if not auteur.is_active:
                    continue
                send_mail_auteur.delay(auteur, livre, 'jour5.html', u'Vous semblez éprouver des difficultés...')
                livre.jour5 = local_dt
                livre.save()

@shared_task(name='batch_jour20')
def batch_jour20(date_de_passage=None):
    """Si le livre a moins de 10 souscriptions après 20 jours de campagne,
    un mail est envoyé à l'auteur pour lui donner des conseils """
    local_dt = check_date(date_de_passage, 'batch_jour20')
    if not local_dt:
        return
    livres = Livre.objects.filter(phase='GETMONEY', is_active=True, date_souscription__lte=date.today()-timedelta(days=20), jour20=None, nb_jours_campagne=60)
    logger.info('BATCH BIBLIOCRATIE batch_jour20 : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        if livre.nb_exemplaires_souscrits <= 10:
            for auteur in livre.auteurs.all():
                if not auteur.is_active:
                    logger.warning(auteur.email + ' est inactif')
                    continue
                send_mail_auteur.delay(auteur, livre, 'jour20.html', u'Vous semblez éprouver des difficultés...')
                livre.jour20 = local_dt
                livre.save()


@shared_task(name='batch_jour30')
def batch_jour30(date_de_passage=None):
    """mail d'encouragement à l'auteur à la moitié de la souscription """
    local_dt = check_date(date_de_passage, 'batch_jour30')
    if not local_dt:
        return
    livres = Livre.objects.filter(phase='GETMONEY', is_active=True, jour30=None)
    logger.info('BATCH BIBLIOCRATIE batch_jour30 : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        if not livre.date_souscription_cron.date() < date.today() - timedelta(days=livre.nb_jours_campagne / 2):
            continue
        auteurs = livre.auteurs.all()
        for auteur in auteurs:
            if not auteur.is_active:
                logger.warning(auteur.email + ' est inactif')
                continue
            send_mail_auteur.delay(auteur, livre, 'jour30.html', u'Vous voilà maintenant à mi-parcours de votre souscription')
            livre.jour30 = local_dt
            livre.save()


@shared_task(name='batch_5_to_end')
def batch_5_to_end(date_de_passage=None):
    """mail d'encouragement à l'auteur 5 jours avant la fin
    de la souscription """
    local_dt = check_date(date_de_passage, 'batch_5_to_end')
    if not local_dt:
        return
    livres = Livre.objects.filter(phase='GETMONEY', is_active=True, five_to_end=None)
    logger.info('BATCH BIBLIOCRATIE batch_5_to_end : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        date_fin = livre.date_souscription_cron + timedelta(days=livre.nb_jours_campagne)
        if date_fin < local_dt - timedelta(days=5):
            continue
        if livre.get_percent() >= 50:
            auteurs = livre.auteurs.all()
            for auteur in auteurs:
                if not auteur.is_active:
                    logger.warning(auteur.email + ' est inactif')
                    continue
                send_mail_auteur.delay(auteur, livre, '5_to_end.html', u'La dernière ligne droite...')
                livre.five_to_end = local_dt
                livre.save()

@shared_task(name='batch_jour40_afer_closed')
def batch_jour40(date_de_passage=None):
    """40 jours après la fin de la campagne, un mail de promotion
     est envoyé à l'auteur """
    local_dt = check_date(date_de_passage, 'batch_jour40_afer_closed')
    if not local_dt:
        return
    livres = Livre.objects.filter(phase='SUCCES', is_active=True, date_closed__lte=date.today()-timedelta(days=40), jour40=None)
    logger.info('BATCH BIBLIOCRATIE batch_jour40_afer_closed : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        auteurs = livre.auteurs.all()
        for auteur in auteurs:
            if not auteur.is_active:
                logger.warning(auteur.email + ' est inactif')
                continue
            send_mail_auteur.delay(auteur, livre, 'jour40_afer_closed.html', u'Votre livre vous plaît ?')
            livre.jour40 = local_dt
            livre.save()

@shared_task(name='batch_souscription85')
def batch_souscription85(date_de_passage=None):
    """mail de félication à lorsque les 85% \de la souscription sont atteint """
    local_dt = check_date(date_de_passage, 'batch_souscription85')
    if not local_dt:
        return
    livres = Livre.objects.filter(phase='GETMONEY', is_active=True, pourcentage_souscription_85=None)
    logger.info('BATCH BIBLIOCRATIE batch_souscription85 : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        if livre.souscription_set.count()>0:
            pourcentage = livre.get_percent()
            if pourcentage >= 85 and pourcentage < 100:
                for auteur in livre.auteurs.all():
                    if auteur.is_active:
                        send_mail_auteur.delay(auteur, livre, 'souscription85.html', u'Vous touchez au but...')
                livre.pourcentage_souscription_85 = local_dt
                livre.save()

@shared_task(name='batch_souscription100')
def batch_souscription100(date_de_passage=None):
    """mail de félication à lorsque les 100% \de la souscription sont atteint """
    local_dt = check_date(date_de_passage, 'batch_souscription100')
    if not local_dt:
        return
    livres = Livre.objects.filter(phase='GETMONEY', is_active=True, pourcentage_souscription_100=None)
    logger.info('BATCH BIBLIOCRATIE batch_souscription100 : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        if livre.souscription_set.count()>0:
            pourcentage = livre.get_percent()
            if pourcentage >= 100 and pourcentage < 200:
                for auteur in livre.auteurs.all():
                    if auteur.is_active:
                        send_mail_auteur.delay(auteur, livre, 'souscription100.html', u'Félicitations, votre objectif est atteint !')
                livre.pourcentage_souscription_100 = local_dt
                livre.save()

@shared_task(name='batch_souscription200')
def batch_souscription200(date_de_passage=None):
    """mail de félication à lorsque les 200% \de la souscription sont atteint """
    local_dt = check_date(date_de_passage, 'batch_souscription200')
    if not local_dt:
        return
    livres = Livre.objects.filter(phase='GETMONEY', is_active=True, pourcentage_souscription_200=None)
    logger.info('BATCH BIBLIOCRATIE batch_souscription200 : {0} livres a traiter'.format(livres.count()))
    for livre in livres:
        if livre.souscription_set.count()>0:
            pourcentage = livre.get_percent()
            if pourcentage >= 200:
                for auteur in livre.auteurs.all():
                    if auteur.is_active:
                        send_mail_auteur.delay(auteur, livre, 'souscription200.html', u'Quel succès...')
                livre.pourcentage_souscription_200 = local_dt
                livre.save()


@shared_task(name='batch_me_rappeler')
def batch_me_rappeler(date_de_passage=None):
    """me rappeler que la campagne de ce livre se termine dans 2 jours """
    local_dt = check_date(date_de_passage, 'batch_me_rappeler')
    if not local_dt:
        return
    rappels = MeRappeler.objects.filter(livre__phase="GETMONEY")

    for rappel in rappels:
        date_fin = rappel.livre.date_souscription_cron + timedelta(days=rappel.livre.nb_jours_campagne)
        if not local_dt > date_fin - timedelta(days=2):
            continue
        if not rappel.user.is_active:
            logger.warning(rappel.user.email + ' est inactif')
            continue
        send_mail_auteur.delay(rappel.user, rappel.livre, 'merappeler.html', unicode(rappel.livre.titre) + u' // Fin de la souscription imminente')
        rappel.delete()


@shared_task(name='batch_mail_auteur_demandes_new_souscription')
def batch_mail_auteur_demandes_new_souscription(date_de_passage=None):
    """envoie un mail à l'auteur quand plus de 20 personnes demandent
    que le livre soit en campagne à nouveau """
    local_dt = check_date(date_de_passage, 'batch_mail_auteur_demandes_new_souscription')
    if not local_dt:
        return

    livres = Livre.objects.annotate(total = Count('demandernewsouscription')).filter(total__gte=settings.SEUIL_DEMANDES_RESOUSCRIPTION, is_active=True)
    logger.info('BATCH BIBLIOCRATIE mail_auteur_demandes_new_souscription : {0} livres à traiter'.format(livres.count()))

    for livre in livres:
        logger.info('BATCH BIBLIOCRATIE mail_auteur_demandes_new_souscription : traitement de {0}'.format(livre.titre.encode('utf-8')))
        if not livre.date_relance_auteur:
            for auteur in livre.auteurs.all():
                if not auteur.is_active:
                    logger.warning(auteur.email + ' est inactif')
                    continue
                send_mail_auteur.delay(auteur, livre, 'mail_auteur_demandes_new_souscription.html', u'Vos lecteurs vous réclament.')

            livre.date_relance_auteur = local_dt
            livre.save()


###########################FIN BATCHS Bibliocratie####################################


###########################TACHES ASYNCHRONES Bibliocratie####################################
@shared_task(name='review_from_bibliocratie')
def review_from_bibliocratie(livre):
    """envoie un mail à bibliocratie quand l'auteur demande à faire
    valider son livre et à l'auteur pour le prevenir qu'il aura une réponse
    dans 24h """
    logger.info('TASK BIBLIOCRATIE review_from_bibliocratie : {0}'.format(livre.titre))
    auteurs = list()
    if livre.date_demande_validation_souscription is None:
        souscription = 'presouscription'
    else:
        souscription = 'souscription'
    for auteur in livre.auteurs.filter(is_active=True):
        auteurs.append(auteur)
        ctx = {
            'livre' : livre,
            'auteur': auteur,
            'souscription': souscription
        }
        send_mail_with_context.delay(auteur.email, ctx, 'validation_par_bibliocratie_auteur.html', u'Projet '+unicode(livre.titre) + u' en cours de validation')
    for staff in settings.BATCH_EMAIL:
        logger.info('TASK BIBLIOCRATIE review_from_bibliocratie envoi admin: {0}'.format(staff[1]))
        if livre.pre_souscription and livre.phase=='FROZEN':
            date_butoire = livre.date_demande_validation_presouscription
        else:
            date_butoire = livre.date_demande_validation_souscription
        ctx = {
            'livre' : livre,
            'auteurs': auteurs,
            'date_butoire': date_butoire + timedelta(hours=24),
            'souscription': souscription
        }
        send_mail_with_context.delay(staff[1], ctx, 'validation_par_bibliocratie_staff.html', u'Projet '+ unicode(livre.titre) + u' en cours de validation')


@shared_task(name='frozen_to_validate')
def frozen_to_validate(livre):
    """envoie un mail à l'auteur pour le prévenir que bibliocratie à
    valider son livre """
    logger.info('TASK BIBLIOCRATIE frozen_to_validate : {0}'.format(livre.titre))
    if livre.pre_souscription:
        date_lancement = livre.date_feedback
    else:
        date_lancement = livre.date_souscription
    for auteur in livre.auteurs.filter(is_active=True):
        ctx = {
            'livre' : livre,
            'auteur': auteur,
            'date_lancement': date_lancement
        }
        send_mail_with_context.delay(auteur.email, ctx, 'frozen_to_validate.html', u'Votre projet est validé')

@shared_task(name='frozfee_to_valfeed')
def frozfee_to_valfeed(livre):
    """ envoie un mail à l'auteur pour le prévenir que bibliocratie à
    valider son livre pour la souscription"""
    logger.info('TASK BIBLIOCRATIE frozfee_to_valfeed : {0}'.format(livre.titre))
    for auteur in livre.auteurs.all():
        send_mail_auteur.delay(auteur, livre, 'frozfee_to_valfeed.html', u'Souscription validée')


@shared_task(name='creatran_to_frozfee')
def creatran_to_frozfee(livre):
    """envoi un mail à l'auteur et à bibliocratie pour les prevenirs de la
    validation en cours """
    logger.info('TASK BIBLIOCRATIE creatran_to_frozfee : {0}'.format(livre.titre))
    auteurs = list()
    for auteur in livre.auteurs.filter(is_active=True):
        auteurs.append(auteur)
        send_mail_auteur.delay(auteur, livre, 'creatran_to_frozfee_auteur.html', u'Souscription en cours de validation')
    for staff in settings.BATCH_EMAIL:
        ctx = {
            'livre' : livre,
            'auteurs': auteurs,
            'date_butoire': livre.date_demande_validation_presouscription + timedelta(hours=24)
        }
        send_mail_with_context.delay(staff[1], ctx, 'creatran_to_frozfee_staff.html', u'Le projet '+ unicode(livre.titre) + u' est valide')


#RECEIVERS Bibliocratie
@shared_task(name='proposition_post_save')
def task_proposition_post_save(proposition):
    logger.debug(u'on_proposition_post_save. Auteur :[%s] Livre:[%s]', unicode(proposition.auteur), proposition.livre.titre)

    if proposition.deleted:
        return

    if not proposition.auteur.is_active:
        return

    #si l'auteur choisi une proposition
    if proposition.chosen:
        return

    #si le livre est en création c'est l'auteur qui est en train d'écrire ses propositions
    if proposition.livre.phase == "CREATION":
        return

    #notification a l'auteur de la proposition
    notification = Notification(image_url=proposition.livre.image_50x50_url(),texte=_("Merci pour votre proposition"),link_url=proposition.livre.url())
    redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
    RedisPublisher(facility='user', users=[proposition.auteur.username.encode('utf-8')]).publish_message(redisMessage)

    #notification broadcast sur le livre
    if not proposition.private:
        redisMessage = RedisMessage(JSONRenderer().render(LivreApiSerializer(proposition.livre).data))
        RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

    #Proposition sauvegardée dans la timeline de celui qui a fait la proposition
    t = Timeline(content_object=proposition, user=proposition.auteur, action='PROPOSITION')
    t.save()

    if not proposition.private:
        for user in proposition.auteur.suivipar.all():
            if not user.is_active:
                continue

            #partage de l'evenement dans la timeline des followers de l'auteur de la proposition
            t.partage.add(user.qui)

            #notification aux followers de l'auteur de la proposition
            if user.qui.userpreference.FollowingNewPropositionNotifyMe:
                if not user.qui.is_active:
                    continue
                notification = Notification(image_url=proposition.livre.image_50x50_url(),link_url=proposition.livre.url(),
                                            texte=proposition.auteur.username.encode('utf-8') + _(" a fait une proposition sur le livre")+ proposition.livre.titre)
                redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
                RedisPublisher(facility='user', users=[user.qui.username.encode('utf-8')]).publish_message(redisMessage)

        #partage de l'evenement dans la timeline de l'auteur livre
        for auteur in proposition.livre.auteurs.all():
            t.partage.add(auteur)

    #mise a jour websocket des timelines
    redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

    #notification aux auteurs du livre
    for auteur in proposition.livre.auteurs.all():
        if auteur!=proposition.auteur:
            notification = Notification(image_url=proposition.livre.image_50x50_url(),texte=proposition.auteur.username.encode('utf-8')+_(" a fait une proposition sur votre livre"),link_url=proposition.livre.url())
            redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
            RedisPublisher(facility='user', users=[auteur.username.encode('utf-8')]).publish_message(redisMessage)

@shared_task(name='commentaire_post_save')
def task_commentaire_post_save(commentaire):
    logger.debug(u'on_commentaire_post_save. Auteur :[%s] Livre:[%s]', unicode(commentaire.user), commentaire.livre.titre)

    redisMessage = RedisMessage(JSONRenderer().render(SouscriptionApiSerializer(commentaire.livre).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)
    #Commentaire sauvegardé dans la timeline de celui qui a fait le commentaire
    t = Timeline(content_object=commentaire, user=commentaire.user, action='COMMENTAIRE')
    t.save()

    for auteur in commentaire.livre.auteurs.all():

        if not auteur.is_active:
            continue

        #partage de l'evenement dans la timeline de l'auteur livre
        t.partage.add(auteur)

        #notification aux auteurs du Livre
        notification = Notification(image_url=commentaire.livre.image_50x50_url(),link_url=commentaire.livre.url(),
                                    texte=commentaire.user.username.encode('utf-8') + _(" a fait un commentaire sur le livre ")+ unicode(commentaire.livre.titre))
        redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
        RedisPublisher(facility='user', users=[auteur.username.encode('utf-8')]).publish_message(redisMessage)

    for user in commentaire.user.suivipar.all():

        if not user.is_active:
            continue

        #partage de l'evenement dans la timeline des followers de l'auteur de la proposition
        t.partage.add(user.qui)

        #notification aux followers de l'auteur du commentaire
        if user.qui.userpreference.FollowingNewCommentaireNotifyMe:

            if not user.qui.is_active:
                continue

            notification = Notification(image_url=commentaire.livre.image_50x50_url(),link_url=commentaire.livre.url(),
                                        texte=commentaire.user.username.encode('utf-8') + _(" a fait un commentaire sur le livre")+ commentaire.livre)
            redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
            RedisPublisher(facility='user', users=[user.qui.username.encode('utf-8')]).publish_message(redisMessage)

    #mise a jour websocket des timelines
    redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

@shared_task(name='timelinecommentaire_post_save')
def task_timeline_commentaire_post_save(commentaire):
    logger.debug(u'on_timeline_commentaire_post_save. Auteur :[%s] user:[%s]', unicode(commentaire.user), unicode(commentaire.timeline.user))

    if commentaire.timeline.user.is_active:
        #notification aux auteurs du Livre si l'auteur du commentaire n'est pas le propriétaire de l'évènement
        if commentaire.user.username.encode('utf-8') != commentaire.timeline.user.username.encode('utf-8'):
            notification = Notification(image_url=commentaire.user.avatar_50x50_url(),link_url=commentaire.user.profil_url(),
                                        texte=commentaire.user.username.encode('utf-8') + _(" a fait un commentaire sur votre profil "))
            redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
            RedisPublisher(facility='user', users=[commentaire.timeline.user.username.encode('utf-8')]).publish_message(redisMessage)

    for user in commentaire.user.suivipar.all():

        if user.qui.is_active and user.qui.userpreference.FollowingNewCommentaireNotifyMe:
            notification = Notification(image_url=commentaire.user.avatar_50x50_url(),link_url=commentaire.user.profil_url(),
                                        texte=commentaire.user.username.encode('utf-8') + _(" a fait un commentaire sur le profil de ")+ commentaire.timeline.user.username)
            redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
            RedisPublisher(facility='user', users=[user.qui.username.encode('utf-8')]).publish_message(redisMessage)

    #mise a jour websocket des timelines
    redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(commentaire.timeline).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)



@shared_task(name='commentaire_post_delete')
def task_commentaire_post_delete(commentaire):
    logger.debug(u'on_commentaire_post_delete. Auteur :[%s] Livre:[%s]', unicode(commentaire.user), commentaire.livre.titre)
    timelines = Timeline.objects.filter(object_id=commentaire.id)
    for timeline in timelines:
        timeline.delete()

@shared_task(name='vote_post_save')
def task_vote_post_save(vote):
    #mise a jour broadcast des jauges du livre
    proposition = vote.proposition.getTypedProposition()

    logger.debug(u'on_vote_post_save. Auteur :[%s] Livre:[%s]', unicode(vote.user), proposition.livre)

    redisMessage = RedisMessage(JSONRenderer().render(LivreApiSerializer(proposition.livre).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

    if not vote.user.is_active:
        return

    #Vote sauvegardé dans la timeline de celui qui a voté
    t = Timeline(content_object=vote, user=vote.user, action='VOTE')
    t.save()

    for user in vote.user.suivipar.all():
        #partage de l'evenement dans la timeline des followers de l'auteur du Vote
        t.partage.add(user.qui)

        #notification aux followers de l'auteur du vote
        if user.qui.userpreference.FollowingNewVoteNotifyMe:
            notification = Notification(image_url=vote.proposition.livre.image_50x50_url(),link_url=vote.proposition.livre.url(),
                                        texte=vote.user.username.encode('utf-8') + _(" a fait un vote sur la presousciption ")+ unicode(vote.proposition.livre.titre))
            redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
            RedisPublisher(facility='user', users=[user.qui.username.encode('utf-8')]).publish_message(redisMessage)

    #mise a jour websocket des timelines
    redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

@shared_task(name='livre_changes_phase')
def task_livre_changes_phase(livre):
    logger.debug(u'on_livre_changes_phase. Livre:[%s] Phase :[%s] ', unicode(livre), livre.phase)

    if livre.phase == 'FROZEN': #creation en attende de validation Bibliocratie
        review_from_bibliocratie.delay(livre)
    elif livre.phase == 'VALIDATE': # creation validee par Bibliocratie. En attente du CRON
        frozen_to_validate.delay(livre)
    elif livre.phase == 'VAL-FEED': #pre-souscription transformee validee par Bibliocratie. En attente du CRON
        frozfee_to_valfeed.delay(livre)
    elif livre.phase == 'CREATRAN': #presouscription transformee ---> on s'en fout
        pass
    elif livre.phase == 'FROZ-FEE': # in review from bibliocratie before campaign
        creatran_to_frozfee.delay(livre)
    #mise a jour broadcast des jauges du livre
    redisMessage = RedisMessage(JSONRenderer().render(SouscriptionApiSerializer(livre).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

    for auteur in livre.auteurs.all():
        if not auteur.is_active:
            continue

        if livre.phase in ['FEEDBACK','GETMONEY','SUCCES','ECHEC']:
            #Livre sauvegardé dans la timeline des auteurs
            t = Timeline(content_object=livre, user=auteur, action=livre.phase)
            if livre.phase == 'SUCCES':
                t.action = 'SUCCES-LIVRE'
            elif livre.phase == 'ECHEC':
                t.action = 'ECHEC-LIVRE'
            t.save()
            for user in auteur.suivipar.all():
                #partage de l'evenement dans la timeline des followers de l'auteur du livre
                t.partage.add(user.qui)

                #notification aux followers de l'auteur
                if livre.phase == 'FEEDBACK':
                    notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                                texte=_("La pre-souscription pour le livre ") + unicode(livre.titre) +_(" a commence"))
                elif livre.phase == 'GETMONEY':
                    notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                                texte=_("Le livre ") + unicode(livre.titre) +_(" est passe en souscription"))
                elif livre.phase == 'SUCCES':
                    notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                                texte=_("Le livre ") + unicode(livre.titre) +_(" est un succes"))
                elif livre.phase == 'ECHEC':
                    notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                                texte=_("Le livre ") + unicode(livre.titre) +_(" est un echec"))
                redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
                RedisPublisher(facility='user', users=[user.username.encode('utf-8')]).publish_message(redisMessage)

            #mise a jour websocket des timelines
            redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
            RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

        #notification envoyée à l'auteur
        if livre.phase == 'CREATION':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" est revenu a l\'etape de creation"))
        elif livre.phase == 'FROZEN':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" est en attente de validation par Bibliocratie"))
        elif livre.phase == 'VALIDATE':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" a ete valide en pre-souscription, en attente du debut de la pre-souscription"))
        elif livre.phase == 'FEEDBACK':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("La pre-souscription pour votre livre ") + unicode(livre.titre) +_(" a commence"))
        elif livre.phase == 'CREA-FEE':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("La pre-souscription pour votre livre ") + unicode(livre.titre) +_(" est fini, vous pouvez effectuer les dernieres modifications"))
        elif livre.phase == 'CREATRAN':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("La presouscription pour votre livre" + unicode(livre.titre) + " est transformee en souscription, elle est toujours editable"))
        elif livre.phase == 'FROZ-FEE':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" est en attente de validation par Bibliocratie"))
        elif livre.phase == 'VAL-FEED':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" a ete valide en souscription, en attente du début de la souscription"))
        elif livre.phase == 'GETMONEY':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" est passe en souscription"))
        elif livre.phase == 'SUCCES':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" est un succes"))
        elif livre.phase == 'ECHEC':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" est un echec"))
        elif livre.phase == 'CANCELLE':
            notification = Notification(image_url=livre.image_50x50_url(),link_url=livre.url(),
                                        texte=_("Votre livre ") + unicode(livre.titre) +_(" est annule"))

        redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
        RedisPublisher(facility='user', users=[auteur.username.encode('utf-8')]).publish_message(redisMessage)


@shared_task(name='follow_post_save')
def task_follow_post_save(follow):
    logger.debug(u'on_follow_post_save. Qui:[%s] Suit :[%s] lien:[%s]', unicode(follow.qui), unicode(follow.suit), follow.lien)
    if (not follow.qui.is_active) or (not follow.suit.is_active):
       return

    #previens une personne qu'elle est suivie
    if follow.lien=='AMI':
        notification = Notification(image_url=follow.qui.avatar_50x50_url(),link_url=follow.qui.profil_url(),
                                    texte=follow.qui.username.encode('utf-8') + _(" vous suit."))
    elif follow.lien=='ENN':
        notification = Notification(image_url=follow.qui.avatar_50x50_url(),link_url=follow.qui.profil_url(),
                                    texte=follow.qui.username.encode('utf-8') + _(" a cesse de vous suivre."))
    redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
    RedisPublisher(facility='user', users=[follow.suit.username.encode('utf-8')]).publish_message(redisMessage)

    #inscription dans la timeline du follower
    t = Timeline(content_object=follow, user=follow.qui, action=follow.lien)
    t.save()

    for user in follow.qui.suivipar.all():
        #partage de l'evenement dans la timeline des followers de follower
        t.partage.add(user.qui)

        #notification des followers de follower
        if user.qui.userpreference.FollowingNewFollowNotifyMe:
            if follow.lien=='AMI':
                notification = Notification(image_url=follow.suit.avatar_50x50_url(),link_url=follow.suit.profil_url(),
                                            texte=follow.qui.username.encode('utf-8') + _(" suit desormais ") + unicode(follow.suit))
            elif follow.lien=='ENN':
                notification = Notification(image_url=follow.suit.avatar_50x50_url(),link_url=follow.suit.profil_url(),
                                            texte=follow.qui.username.encode('utf-8') + _(" a arrete de suivre ") + unicode(follow.suit))
            redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
            RedisPublisher(facility='user', users=[user.qui.username.encode('utf-8')]).publish_message(redisMessage)


    #partage de l'evenement dans la timeline du followee
    t.partage.add(follow.suit)

    #mise a jour websocket des timelines
    redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

@shared_task(name='souscription_changes_status')
def task_souscription_changes_status(souscription):
    logger.debug(u'on_souscription_changes_status. Client :[%s] Livre:[%s]  Etat:[%s]', unicode(souscription.panier.client), souscription.livre.titre, souscription.etat)

    #Mise a jour des jauges de livres
    redisMessage = RedisMessage(JSONRenderer().render(SouscriptionApiSerializer(souscription.livre).data))
    RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

    if not souscription.panier.client.is_active:
       return

    if souscription.etat=='SUC':
        #inscription du succes dans la timeline de l'acheteur
        t = Timeline(content_object=souscription, user=souscription.panier.client, action='SUCCES-SOUSCRIPTION')
        t.save()

        #notification de l'acheteur
        notification = Notification(image_url=souscription.livre.image_50x50_url(),link_url=souscription.livre.url(),
                                    texte= _("La souscription sur le livre ")+ unicode(souscription.livre.titre) + _(" vient de reussir "))
        redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
        RedisPublisher(facility='user', users=[souscription.panier.client.username.encode('utf-8')]).publish_message(redisMessage)

        #mise a jour websocket des timelines
        redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
        RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

    if souscription.etat=='ECH':
        #inscription de l'echec dans la timeline de l'acheteur
        t = Timeline(content_object=souscription, user=souscription.panier.client, action='ECHEC-SOUSCRIPTION')
        t.save()

        #notification de l'acheteur
        notification = Notification(image_url=souscription.livre.image_50x50_url(),link_url=souscription.livre.url(),
                                    texte= _("La souscription sur le livre ")+ unicode(souscription.livre.titre) + _(" a echoue "))
        redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
        RedisPublisher(facility='user', users=[souscription.panier.client.username.encode('utf-8')]).publish_message(redisMessage)

        #mise a jour websocket des timelines
        redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
        RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)



@shared_task(name='commande_changes_status')
def task_commande_changes_status(commande):
    logger.debug(u'commande_changes_status. Client :[%s] Status:[%s]', unicode(commande.client), commande.get_etat_display())

    #refresh du panier
    if commande.client:
        if not commande.client.is_active:
            return
        #On Envoie le nouveau panier au client
        panier=commande.client.get_panier()
        redisMessage = RedisMessage(JSONRenderer().render(PanierApiSerializer(panier).data))
        RedisPublisher(facility='user', users=[commande.client.username.encode('utf-8')]).publish_message(redisMessage) ##encode error?

    #Mise a jour des timeline
    if commande.etat=='PAY':
        #Achats sauvegardés dans la timeline de l'auteur
        for souscription in commande.souscription_set.all():
            souscription.souscription_pourcent = souscription.livre.get_percent()
            souscription.save()
            #Achats sauvegardés dans la timeline de l'acheteur
            t = Timeline(content_object=souscription, user=commande.client, action='ACHAT')
            t.save()
            #mise a jour websocket de la timeline de l'acheteur
            redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
            RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

            for user in commande.client.suivipar.all():
                #partage de l'evenement dans la timeline des followers de l'acheteur
                t.partage.add(user.qui)

                #On notifie les followers de l'acheteur
                if user.qui.userpreference.FollowingNewCommandeNotifyMe:
                    notification = Notification(image_url=souscription.livre.image_50x50_url(),link_url=souscription.livre.url(),
                                                texte= commande.client.username.encode('utf-8') + _("viens d'acheter ")+
                                                       unicode(souscription.quantite) + _(" exemplaires du livre ") + unicode(souscription.livre.titre))
                    redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
                    RedisPublisher(facility='user', users=[user.qui.username.encode('utf-8')]).publish_message(redisMessage)

            for auteur in souscription.livre.auteurs.all():
                #partage de l'evenement dans la timeline des auteurs
                t.partage.add(auteur)

                #On notifie l'auteur
                notification = Notification(image_url=souscription.livre.image_50x50_url(),link_url=souscription.livre.url(),
                                            texte= commande.client.username.encode('utf-8') + _("viens d'acheter ")+
                                                   unicode(souscription.quantite) + _(" exemplaires de votre votre livre ") + unicode(souscription.livre.titre))
                redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
                RedisPublisher(facility='user', users=[auteur.username.encode('utf-8')]).publish_message(redisMessage)

            #mise a jour websocket des timelines
            redisMessage = RedisMessage(JSONRenderer().render(TimelineApiSerializer(t).data))
            RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

    else:
        if commande.etat=='ECH' or commande.etat=='ANL':
            if commande.etat=='ECH':
                notification = Notification(image_url=commande.client.avatar_50x50_url(),link_url=commande.client.profil_url(),
                                            texte=_("Commande echouee"))
            elif commande.etat=='ANL':
                notification = Notification(image_url=commande.client.avatar_50x50_url(),texte=_("Commande annulee"))

            if commande.client:
                #notification envoyée au client
                redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
                RedisPublisher(facility='user', users=[commande.client.username.encode('utf-8')]).publish_message(redisMessage)


@shared_task(name='user_disconnected')
def task_user_disconnected(user):
    logger.debug(u'on_user_disconnected. User:[%s]', unicode(user))

    #notifie l'utilisateur qu'il a été deconnecté
    notification = Notification(image_url=user.avatar_50x50_url(),link_url=user.profil_url(),
                                texte=_("Votre session a expire "),reload=True)
    redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
    RedisPublisher(facility='user', users=[user.username.encode('utf-8')]).publish_message(redisMessage)

@shared_task(name='souscription_post_delete')
def task_souscription_post_delete(souscription):
    logger.debug(u'on_souscription_post_delete. Client :[%s] Livre:[%s]  Etat:[%s]', unicode(souscription.panier.client), unicode(souscription.livre.titre), souscription.etat)

    if souscription.etat=='ENC':
        redisMessage = RedisMessage(JSONRenderer().render(SouscriptionApiSerializer(souscription.livre).data))
        RedisPublisher(facility='broadcast', broadcast=True).publish_message(redisMessage)

@shared_task(name='commande_post_delete')
def task_commande_post_delete(commande):
    logger.debug(u'commande_post_delete. Client :[%s] Status:[%s]', unicode(commande.client), commande.etat)

    if commande.etat=='TMP' or commande.etat=='ECH' or commande.etat=='ARR':
        try:
            panier=commande.client.get_panier()
            redisMessage = RedisMessage(JSONRenderer().render(PanierApiSerializer(panier).data))
            RedisPublisher(facility='user', users=[commande.client.username.encode('utf-8')]).publish_message(redisMessage)
        except:
            pass


@shared_task(name='task_suggestions')
def task_suggestions(user):
    """ajout des sugestions de livre et d'utilisateur dans la timeline de
    l'utilisateur """
    timelines = user.owned_timelines.order_by('-timestamp')
    i=0
    stop=False
    if timelines.count()==0:
        #pas de timeline? pas de suggestions....
        return

    while not stop:
        t = timelines[i]
        if t.action=='SUGGESTION_USER' or t.action=='SUGGESTION_LIVRE':
            stop=True
        if i>settings.TIMELINE_ELEMENTS_BEGORE_SUGGESTION:
            stop=True
        i+=1
        if i>=timelines.count():
            stop=True
    if i>settings.TIMELINE_ELEMENTS_BEGORE_SUGGESTION and i<timelines.count():
        stop=False
        while not stop:
            t = timelines[i]
            if t.action=='SUGGESTION_USER':
                t = Timeline(content_object=user.recommendation_livre(), user=user, action='SUGGESTION_LIVRE',private=True)
                t.save()
                stop=True
            elif t.action=='SUGGESTION_LIVRE':
                t = Timeline(content_object=user.recommendation_user(), user=user, action='SUGGESTION_USER',private=True)
                t.save()
                stop=True
            i +=1
            if i>=len(timelines):
                stop=True
                t = Timeline(content_object=user.recommendation_user(), user=user, action='SUGGESTION_USER',private=True)
                t.save()

@shared_task(name='task_detecte_vieux_livres')
def task_detecte_vieux_livres(date_de_passage=None):
    """vérifie les livres en campagne. Si ils sont en campagne depuis plus
    de settings.NB_JOURS_NOUVEAU_LIVRE jours, on enlève l'état NOUVEAU du livre """
    local_dt = check_date(date_de_passage, 'batch_detecte_vieux_livres')
    if not local_dt:
        return

    livres = Livre.objects.filter(etat__in=['NOUVEAU'])
    logger.info('BATCH BIBLIOCRATIE detecte_vieux_livres : {0} livres à traiter'.format(livres.count()))

    for livre in livres:
        # logger.info('BATCH BIBLIOCRATIE detecte_nouveaux_livres : traitement de {0}'.format(livre.titre.encode('utf-8')))
        date_plus_nouveau = livre.date_souscription + relativedelta(days=+settings.NB_JOURS_NOUVEAU_LIVRE)
        if date_plus_nouveau < local_dt:
            logger.info(livre.titre.encode('utf-8') + ' est ANCIEN')
            livre.etat = ''
            livre.save()
