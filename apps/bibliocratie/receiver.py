# -*- coding: utf-8 -*-
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .tasks import *
from .models import *
from .signals import commande_changes_status, souscription_changes_status, livre_changes_phase, user_disconnected

@receiver(commande_changes_status)
def on_commande_changes_status(sender, **kwargs):
    commande=kwargs['commande']
    task_commande_changes_status.delay(commande)

@receiver(post_delete, sender=Commande)
def on_commande_post_delete(sender, **kwargs):
    commande=kwargs['instance']
    task_commande_post_delete.delay(commande)


@receiver(souscription_changes_status)
def on_souscription_changes_status(sender, **kwargs):
    souscription=kwargs['souscription']
    task_souscription_changes_status.delay(souscription)

@receiver(post_save, sender=CharProposition)
@receiver(post_save, sender=TextProposition)
@receiver(post_save, sender=ImageProposition)
@receiver(post_save, sender=NumberProposition)
def on_proposition_post_save(sender, **kwargs):
    proposition=kwargs['instance']
    task_proposition_post_save.delay(proposition)

@receiver(post_save, sender=Commentaire)
def on_commentaire_post_save(sender, **kwargs):
    commentaire=kwargs['instance']
    task_commentaire_post_save.delay(commentaire)

@receiver(post_delete, sender=Commentaire)
def on_commentaire_post_delete(sender, **kwargs):
    commentaire=kwargs['instance']
    task_commentaire_post_delete.delay(commentaire)    

@receiver(post_save, sender=Vote)
def on_vote_post_save(sender, **kwargs):
    vote=kwargs['instance']
    task_vote_post_save.delay(vote)

@receiver(livre_changes_phase)
def on_livre_changes_phase(sender, **kwargs):
    livre = kwargs['livre']
    task_livre_changes_phase.delay(livre)

@receiver(post_save, sender=Follow)
def on_follow_post_save(sender, **kwargs):
    follow=kwargs['instance']
    if follow.lien=="":
        return
    task_follow_post_save.delay(follow)

@receiver(user_disconnected)
def on_user_disconnected(sender, **kwargs):
    user=kwargs['user']
    task_user_disconnected.delay(user)

@receiver(post_save, sender=TimelineCommentaire)
def on_timeline_commentaire_post_save(sender, **kwargs):
    timeline_commentaire=kwargs['instance']
    task_timeline_commentaire_post_save.delay(timeline_commentaire)

@receiver(post_save, sender=Timeline)
def on_timeline_post_save(sender, **kwargs):
    timeline=kwargs['instance']
    logger.debug('on_timeline_post_save')
    task_suggestions.delay(timeline.user)