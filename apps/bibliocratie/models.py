# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime, timedelta
from timedelta.fields import TimedeltaField
import logging
import pytz
import math
import random
from django.contrib import messages
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.utils import timezone
from django.core.validators import MaxLengthValidator
from django.db import models
from django_countries.fields import CountryField
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail.message import EmailMessage
from django.db.models import Max, Avg
from django.template.defaultfilters import slugify
from django.contrib.staticfiles import finders
from sorl.thumbnail import ImageField, get_thumbnail, default
from sorl.thumbnail.images import ImageFile
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.template.loader import get_template
from django.template import Context
from suds.client import Client
from redactor.fields import RedactorField
from jsonfield import JSONField
from exceptions import NotCalculableException
from django.contrib.staticfiles.templatetags.staticfiles import static
logger = logging.getLogger(__name__)

from django.db import models

from redactor.fields import RedactorField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import AbstractUser


from bibliocratie.signals import commande_changes_status, souscription_changes_status, livre_changes_phase


class BiblioUser(AbstractUser):
    """
    Classe des utilisateurs de Bibliocratie
    """
    slug = models.SlugField(_('slug'), max_length=60, blank=True,unique=True)
    biographie = RedactorField(verbose_name=_('Biographie'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    avatar = ImageField(upload_to='avatars',blank=True)
    site_internet = models.URLField(blank=True)
    lieu = models.CharField(max_length=254, blank=True)
    pref_actu = models.BooleanField(verbose_name=_('Actu, Politique et Societe'),default=False,blank=True)
    pref_adol = models.BooleanField(verbose_name=_('Adolescents'),default=False,blank=True)
    pref_art = models.BooleanField(verbose_name=_('Art, Musique et Cinema'),default=False,blank=True)
    pref_bd = models.BooleanField(verbose_name=_('Bandes dessinees'),default=False,blank=True)
    pref_beau = models.BooleanField(verbose_name=_('Beaux livres'),default=False,blank=True)
    pref_cuisine = models.BooleanField(verbose_name=_('Cuisine et Vins'),default=False,blank=True)
    pref_dict = models.BooleanField(verbose_name=_('Dictionnaires, langues et encyclopedies'),default=False,blank=True)
    pref_droit = models.BooleanField(verbose_name=_('Droit'),default=False,blank=True)
    pref_entreprise = models.BooleanField(verbose_name=_('Economie et entreprise'),default=False,blank=True)
    pref_erotisme = models.BooleanField(verbose_name=_('Erotisme'),default=False,blank=True)
    pref_esoterisme = models.BooleanField(verbose_name=_('Esoterisme et Paranormal'),default=False,blank=True)
    pref_etude = models.BooleanField(verbose_name=_('Etudes superieures'),default=False,blank=True)
    pref_famille = models.BooleanField(verbose_name=_('Bien-etre'),default=False,blank=True)
    pref_fantaisie = models.BooleanField(verbose_name=_('Fantaisie et Terreur'),default=False,blank=True)
    pref_histoire = models.BooleanField(verbose_name=_('Histoire'),default=False,blank=True)
    pref_humour = models.BooleanField(verbose_name=_('Humour'),default=False,blank=True)
    pref_informatique = models.BooleanField(verbose_name=_('Informatique et Internet'),default=False,blank=True)
    pref_litterature = models.BooleanField(verbose_name=_('Litterature'),default=False,blank=True)
    pref_sentiment = models.BooleanField(verbose_name=_('Litterature sentimentale'),default=False,blank=True)
    pref_enfant = models.BooleanField(verbose_name=_('Jeunesse'),default=False,blank=True)
    pref_loisirs = models.BooleanField(verbose_name=_('Loisirs creatifs, decoration et bricolage'),default=False,blank=True)
    pref_manga = models.BooleanField(verbose_name=_('Manga'),default=False,blank=True)
    pref_nature = models.BooleanField(verbose_name=_('Nature et animaux'),default=False,blank=True)
    pref_policier = models.BooleanField(verbose_name=_('Policier et Suspense'),default=False,blank=True)
    pref_religion = models.BooleanField(verbose_name=_('Religions et Spiritualites'),default=False,blank=True)
    pref_sciencefi = models.BooleanField(verbose_name=_('Science-Fiction'),default=False,blank=True)
    pref_sciencehu = models.BooleanField(verbose_name=_('Sciences humaines'),default=False,blank=True)
    pref_sciencete = models.BooleanField(verbose_name=_('Sciences, Techniques et Medecine'),default=False,blank=True)
    pref_scolaire = models.BooleanField(verbose_name=_('Scolaire et Parascolaire'),default=False,blank=True)
    pref_sport = models.BooleanField(verbose_name=_('Sports et passions'),default=False,blank=True)
    pref_tourisme = models.BooleanField(verbose_name=_('Tourisme et Voyages'),default=False,blank=True)
    pref_photo = models.BooleanField(verbose_name=_('Photographie'),default=False,blank=True)

    need_more_info = models.BooleanField(default=False)

    def class_name(self):
        return "BiblioUser"

    @property
    def nom(self):
        return self.adresse.nom

    @property
    def prenom(self):
        return self.adresse.prenom

    @property
    def adresse(self):
        try:
            return self.adresse_set.get(type='CLIENT')
        except:
            return None

    def avatar_50x50_url(self):
        dimensions = "50x50"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': False, 'upscale': False, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.avatar, dimensions, **options).url
        except:
            return static('images/anonymous.png')

    def avatar_200x200_url(self):
        dimensions = "200x200"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': False, 'upscale': False, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.avatar, dimensions, **options).url
        except:
            return static('images/anonymous.png')

    def display_name(self):
        if self.username:
            return unicode(self.username)
        return unicode(self.email)

    def profil_url(self):
        try:
            return reverse('profil_detail', args=[self.slug])
            # return ''.join(['http://', get_current_site(None).domain, reverse('profil_detail', args=[self.slug])])
        except:
            pass

    def __unicode__(self):
        return self.display_name()

    def save(self, *args, **kwargs):
        # if not self.id:
        #     #Only set the slug when the object is created.

        #Le slug est généré à partir du nom d'auteur ou alors a partir de l'email
        if self.username!="":
            slug_base = self.username[:60]
        else:
            slug_base = self.email.split('@')[0]

        slug_try=slugify(slug_base)
        #On verifie que ce slug n'existe pas déjà
        users = BiblioUser.objects.filter(slug=slug_try, is_active=True)

        #si oui on ajoute un index au slug généré
        if users.count()==0 or (users.count()==1 and users.first().email==self.email):
            self.slug=slug_try
        else:
            slug_libre = False
            index=1
            while not slug_libre:
                slug_try_index = slug_try + '_' + str(index)
                nb_user = BiblioUser.objects.filter(slug=slug_try_index, is_active=True).count()
                if nb_user==0:
                    slug_libre=True
                index += 1
            self.slug=slug_try_index

        if self.username=="":
            self.username=self.slug
        else:
            #on vérifie que ce nom d'auteur n'est pas déja utilisé
            users = BiblioUser.objects.filter(username=self.username, is_active=True)

            if not (users.count()==0 or (users.count()==1 and users.first().email==self.email)):
                username_try=self.username
                username_libre = False
                index=1
                while not username_libre:
                    username_try_index = username_try + '_' + str(index)
                    nb_user = BiblioUser.objects.filter(username=username_try_index, is_active=True).count()
                    if nb_user==0:
                        username_libre=True
                    index += 1
                self.username=username_try_index
        self.username = self.username[:30]
        super(BiblioUser, self).save(*args, **kwargs)
        #On vérifie qu'il a une adresse, sinon on en crée une

        adresse, created = Adresse.objects.get_or_create(client=self,type='CLIENT')

        #On vérifie qu'il a une préférence sinon on en crée une

        preference, created = UserPreference.objects.get_or_create(client=self)

    def delete(self, using=None):
        adresse = self.adresse
        adresse.delete()
        super(BiblioUser, self).delete(using=None)


    def get_panier(self):
        try:
            panier = self.commande_set.get(etat='TMP')
        except:
            try:
                panier = Commande(etat='TMP', client = self)
            except:
                panier=None
        return panier

    def livres_suivis(self):
        #livres ecrits
        livres_ecrits = self.livre_set.all()
        #Livres achetes mis en panier etc...
        livres_achetes = Livre.objects.filter(souscription__panier__client=self, is_active=True)
        #Livres ou l'utilisateur a fait des propositions
        livres_prop = Livre.objects.filter(proposition__vote__user=self, is_active=True)
        #Livres ou l'utilisateur a fait des votes
        livres_vote = Livre.objects.filter(proposition__auteur=self, is_active=True)
        qset = livres_ecrits | livres_achetes | livres_prop | livres_vote
        return qset.distinct().order_by('-date_souscription', '-date_feedback','date_closed')

    def recommendation_livre(self, livre = None):
        recommendation = self.recommendations_livres(livre=livre, quantite=1)
        return recommendation.pop()['livre']

    def recommendations_livres(self, livre=None, quantite=1):
        i=1
        list=[]
        souscriptions = Livre.objects.filter(phase='GETMONEY',is_active=True)
        if len(souscriptions)<=1:
            return [{'livre':livre,'rang':100}]
        while i<=quantite:
            while True:
                id = random.randint(0, len(souscriptions)-1)
                suggestion = souscriptions[id]
                if suggestion!=livre:
                    break
            rang = random.randint(1, 100)
            list.append({'livre':suggestion,'rang':rang})
            i += 1
        def comp(v1, v2):
            if v1['rang']<v2['rang']:
                return 1
            elif v1['rang']>v2['rang']:
                return -1
            else:
                return 0
        list.sort(cmp=comp)
        return list

    def recommendation_user(self):
        recommendation = self.recommendations_users(quantite=1)
        return recommendation.pop()['user']

    def recommendations_users(self, quantite=1):
        i=1
        list=[]
        users = BiblioUser.objects.filter(is_active=True)
        while i<=quantite:
            while True:
                id = random.randint(0, len(users)-1)
                user = users[id]
                if user!=self:
                    break
            rang = random.randint(1, 100)
            list.append({'user':user,'rang':rang})
            i += 1
        def comp(v1, v2):
            if v1['rang']<v2['rang']:
                return 1
            elif v1['rang']>v2['rang']:
                return -1
            else:
                return 0
        list.sort(cmp=comp)
        return list


@receiver(post_delete, sender=BiblioUser)
def on_user_post_delete(sender, **kwargs):
    user=kwargs['instance']
    adresse = user.adresse
    if adresse:
        adresse.delete()


class Adresse(models.Model):
    # Translators: TYPE_CHOICES de Adresse
    client = models.ForeignKey(BiblioUser)
    commande = models.ForeignKey("Commande", null=True)
    TYPES = (
        ('CLIENT', 'client'),
        ('FACT', 'facturation'),
        ('LIVR', 'livraison'),
    )
    type = models.CharField(max_length=6, choices=TYPES)
    prenom = models.CharField(_('Prenom'), max_length=50, blank=True)
    nom = models.CharField(_('Nom'), max_length=50, blank=True)
    entreprise = models.CharField( max_length=100, blank=True)
    adresse = models.CharField(_('Addresse'), max_length=100, blank=True)
    complement_adresse = models.CharField(_("Complement d'Addresse"), max_length=100, blank=True)
    code_postal = models.CharField(_('Code postal'), max_length=10, blank=True)
    ville = models.CharField(_('Ville'), max_length=100, blank=True)
    pays = CountryField(blank=True)
    phone = models.CharField(_('Telephone'), max_length=30, blank=True)

    def __unicode__(self):
        if self.type=='CLIENT':
            return u'Adresse '+ self.get_type_display()+' de ' + unicode(self.client)
        if self.type=='FACT':
            return u"Adresse de facturation - " + unicode(self.commande)
        if self.type=='LIVR':
            return u"Adresse de livraison - " + unicode(self.commande)
        return "Adresse orpheline"

    def copy(self,adresse):
        if adresse==None:
            return
        self.prenom=adresse.prenom
        self.nom=adresse.nom
        self.entreprise=adresse.entreprise
        self.adresse=adresse.adresse
        self.complement_adresse=adresse.complement_adresse
        self.code_postal=adresse.code_postal
        self.ville=adresse.ville
        self.pays=adresse.pays
        self.phone=adresse.phone
        self.save()


class UserPreference(models.Model):
    client = models.OneToOneField(BiblioUser)
    #achat
    FollowingNewCommandeNotifyMe = models.BooleanField(default=True)
    #presouscription
    FollowingNewPropositionNotifyMe = models.BooleanField(default=True)
    FollowingNewCommentaireNotifyMe = models.BooleanField(default=True)
    FollowingNewVoteNotifyMe = models.BooleanField(default=True)
    #follow. Est-ce que je suis notifie des new follow des gens que je follow
    FollowingNewFollowNotifyMe = models.BooleanField(default=True)
    FollowingOnlineNotifyMe = models.BooleanField(default=True)

    def __unicode__(self):
        return 'Preferences de ' + unicode(self.client)


class Follow(models.Model):
    qui = models.ForeignKey(BiblioUser, related_name='suit')
    suit = models.ForeignKey(BiblioUser, related_name='suivipar')
    TYPES_FOLLOW = (
        ('AMI', _('Ami')),
        ('ENN', _('Ennemi')),
    )
    lien = models.CharField(_('Lien'), max_length=20, choices=TYPES_FOLLOW)
    class Meta:
        unique_together = (("qui", "suit"),)
    def __unicode__(self):              # __unicode__ on Python 2
        return self.qui.email+"-"+unicode(_( "suit" ))+"-"+self.suit.email + unicode(_("comme")) + self.get_lien_display()

class Timeline(models.Model):
    user = models.ForeignKey(BiblioUser,related_name="owned_timelines") #"owned-timelines"
    partage = models.ManyToManyField(BiblioUser, related_name="shared_timelines") #"shared-timelines"
    timestamp = models.DateTimeField(default=timezone.now,db_index=True)
    action = models.SlugField()
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    private = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super(Timeline,self).__init__( *args, **kwargs)

    def __unicode__(self):              # __unicode__ on Python 2
        paris = pytz.timezone('Europe/Paris')
        self.timestamp=self.timestamp.replace(tzinfo=pytz.utc)
        self.timestamp.astimezone(paris)
        return self.user.email+"-"+unicode(self.timestamp.astimezone(paris))+"-"+self.action


class TimelineCommentaire(models.Model):
    user = models.ForeignKey(BiblioUser)
    contenu = models.CharField(max_length=400)
    date = models.DateTimeField(default=timezone.now)
    timeline = models.ForeignKey(Timeline, blank=True)

    def __unicode__(self):
        return self.contenu


class Notification(models.Model):
    user = models.ForeignKey(BiblioUser)
    image_url = models.URLField(blank=True)
    link_url = models.URLField(blank=True)
    texte = models.CharField(max_length=255, blank=True)
    reload = models.BooleanField(default=False)

class PanierManager(models.Manager):
    def getUserPanier(self,request):
        if request.user.is_authenticated():
            panier = request.user.get_panier()
        else:
            try:
                panier = Commande.objects.get(etat='TMP', session = request.session.session_key)
            except:
                try:
                    Commande.objects.get(etat='REF', session = request.session.session_key)
                except:
                    try:
                        panier = self.commande_set.get(etat='ANL')
                    except:
                        try:
                            panier = Commande(etat='TMP', session = request.session.session_key)
                        except:
                            panier=None
                            #raise Exception("Impossible de recuperer la cle de session")
        return panier


class Commande(models.Model):
    PAYLINE_PAIEMENT_ACCEPTE, PAYLINE_PAIEMENT_ARRETE, PAYLINE_PAIEMENT_REFUSE, PAYLINE_PAIEMENT_PENDING = range(4)
    # Translators: ETAT_COMMANDES de Commande
    ETAT_COMMANDES = (
        ('TMP', _('En Cours')),
        ('VAL', _('Validation paiement')),
        ('PEN', _('Pending')),
        ('PAY', _('Paye')),
        ('REF', _('Refus Paiement')),
        ('ARR', _('Arrete')),
    )

    client = models.ForeignKey(BiblioUser, null=True)
    etat = models.CharField(max_length=3, choices=ETAT_COMMANDES, default='TMP',db_index=True)
    session = models.CharField(max_length=32, blank=True,db_index=True)
    no_commande = models.PositiveIntegerField(_("Commande Number"), default=None, null=True,blank=True, db_index=True)
    livraison_autre_adresse = models.BooleanField(default=False)
    payline_token = models.CharField(max_length=50, blank=True, default=None,db_index=True)
    mail_paye_envoye = models.BooleanField(verbose_name=_("Un mail de confirmation a ete envoye a l'acheteur"),default = False)
    pays_livraison = models.CharField( default='FR',max_length=2)
    transaction_id = models.CharField(max_length=50, blank=True, default=None)
    infos = models.TextField(default='',blank=True)
    montant = models.FloatField(verbose_name=_("Montant"),default=-1) #montant est renseigné des que le panier est payé
    date = models.DateTimeField(default=timezone.now,db_index=True)
    objects = PanierManager()

    def __init__(self, *args, **kwargs):
        self.pays_livraison = 'FR'
        super(Commande,self).__init__( *args, **kwargs)

    def __unicode__(self):
        try:
            return u'Commande %s : user : %s etat: %s [%s]' % (self.no_commande, self.client.email, self.get_etat_display(), self.detail())
        except:
            return "Panier anonyme " + self.detail()

    def addSouscription(self, livre_id, quantite=1):
        if self.montant!=-1:
            raise Exception("Impossible d'ajouter une souscription du panier : Le panier est déjà figé")
        livre = Livre.objects.get(id=livre_id, is_active=True)
        try:
            souscription = self.souscription_set.get(etat='TMP', livre=livre, panier=self)
            souscription.quantite +=quantite
        except ObjectDoesNotExist:
            souscription = Souscription(etat='TMP', livre=livre, panier=self, quantite=quantite)
        souscription.save()

    def removeLivre(self, livre_id):
        if self.montant!=-1:
            raise Exception("Impossible d'enlever une souscription du panier : Le panier est déjà figé")
        livre = Livre.objects.get(id=livre_id, is_active=True)
        try:
            souscription = self.souscription_set.get(etat='TMP', livre=livre, panier=self)
            if souscription.quantite >1 :
                souscription.quantite-=1
                souscription.save()
            else:
                souscription.delete()
        except ObjectDoesNotExist:
            pass

    def nbArticles(self):
        return self.souscription_set.count()


    def detail(self):
        detail = ""
        for souscription in self.souscription_set.all():
            detail += "{" + unicode(souscription) +"}"
        return detail

    TROIS_EUROS_SHIPPING_COUNTRY = ['DE','AT','BE','BG','CY','HR','DK','ES','EE','FI','GR','HU','IT',
                                'IE','LV','LT','LU','MT','NL','PL','PT','RO','GB','CZ','SK','SI',
                                'SE']

    def get_frais_envoi(self):
         if self.pays_livraison:
            if self.pays_livraison == 'FR':
                return 0
            frais=0
            if self.pays_livraison in self.TROIS_EUROS_SHIPPING_COUNTRY:
                tarif_unit = 3
            else:
                tarif_unit = 5
            for souscription in self.souscription_set.all():
                frais+= tarif_unit * souscription.quantite
            return frais
         return 0


    def addDiscount(self, discount):
        if self.montant!=-1:
            raise Exception("Impossible d'ajouter une discount au panier : Le panier est déjà figé")
        try:
            discount = self.discount_set.get(panier=self, discount=discount)
            raise Exception("discount deja dans le panier")
        except ObjectDoesNotExist:
            #on compte combien de fois ce code a ete utilise
            nb_use = Discount.objects.filter(discount=discount).count()
            if nb_use>=discount.quantity:
                raise Exception("max d'utilisation du code atteint")

            discount = Discount(panier=self,discount=discount)
            discount.get_reduction()
            discount.save()

    def setPaysLivraison(self, pays):
        self.pays_livraison=pays
        super(Commande, self).save()

    def copy(self, panier):
        if type(panier)!=Commande:
            raise Exception("Commande ne peut copier que des commandes")

        for souscription in panier.souscription_set.all():
            copy_souscription=Souscription()
            copy_souscription.copy(souscription)
            copy_souscription.panier=self
            copy_souscription.merged=True
            copy_souscription.save()

        for discount in panier.discount_set.all():
            copy_discount=Discount()
            copy_discount.copy(discount)
            copy_discount.panier=self
            copy_discount.save()

        panier.montant = self.montant

        # for inscription in panier.inscription_set.all():
        #     copy_inscription=Inscription()
        #     copy_inscription.copy(copy_inscription)
        #     copy_inscription.panier=self
        #     copy_inscription.merged=self
        #     copy_inscription.save()


    @property
    def total_sans_discount_ni_taxes(self):
        total=0
        for souscription in self.souscription_set.all():
            total+=souscription.prix
        # for atelier in self.atelier_set.all():
        #     total+=atelier.prix
        return total

    @property
    def adresse_fact(self):
        try:
            return self.adresse_set.get(type='FACT')
        except:
            return None

    @property
    def adresse_livr(self):
        try:
            return self.adresse_set.get(type='LIVR')
        except:
            return None

    def valider(self):
        "on valide le panier, en attendant la confirmation de paiement"
        self.etat = 'VAL'
        self.montant = self.calcule_prix()
        self.save()

    def payer(self, transaction_id):
        self.etat = 'PAY'
        self.transaction_id=transaction_id
        if self.montant==-1:
            self.montant = self.calcule_prix()
        self.save()

    def annuler(self):
        # passe de l'etat "panier" a l'etat "annule".
        self.etat = 'ARR'
        self.save()
        for souscription in self.souscription_set.all():
            souscription.annuler()

    def refuser(self):
        # passe de l'etat "panier" a l'etat "echoue".
        self.etat = 'REF'
        self.save()
        for souscription in self.souscription_set.all():
            souscription.annuler()

    def pending(self):
        self.etat = "PEN"
        self.save()

    def reset(self):
        self.etat='TMP'
        self.save()

    @property
    def prix(self):
        if self.montant!=-1:
            return self.montant
        else:
            return self.calcule_prix()


    def calcule_prix(self):
        prix_euros = 0
        for souscription in self.souscription_set.all():
            prix_euros += souscription.prix
        for discount in self.discount_set.all():
            prix_euros+= discount.get_reduction()
        prix_euros+=self.get_frais_envoi()
        return prix_euros


    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, date=None):
        try:
            ancien_etat= Commande.objects.get(id=self.id).etat
        except:
            ancien_etat=None
        if self.no_commande==None:
            no_commande_max_dict=Commande.objects.all().aggregate(Max('no_commande'))
            if no_commande_max_dict['no_commande__max']==None:
                no_commande=settings.FIRST_COMMANDE_NUMBER
            else:
                no_commande=no_commande_max_dict['no_commande__max']
            self.no_commande = no_commande+1

        if date:
            self.date=date

        if self.payline_token==None:
            self.payline_token=""

        if self.transaction_id==None:
            self.transaction_id=""

        super(Commande, self).save(force_insert, force_update, using, update_fields=None)
        if self.adresse_fact==None:
            if self.client:
                adresse_user = self.client.adresse
                adresse_fact = Adresse(client=self.client,type="FACT",commande=self)
                adresse_fact.copy(adresse_user)
                adresse_fact.save()
        if self.adresse_livr==None:
            if self.client:
                adresse_livr = Adresse(client=self.client,type="LIVR",commande=self)
                adresse_livr.save()
        if not ancien_etat or (ancien_etat and ancien_etat!=self.etat):
            if date:
                maintenant = date
            else:
                maintenant = timezone.now()
            h = CommandeHistory(commande=self, date=maintenant, etat=self.etat)
            h.save()
            if ancien_etat:
                if self.etat=='PAY':
                    for souscription in self.souscription_set.all():
                        souscription.valider()
                if self.etat=='REF' or self.etat=='ARR' :
                    if self.souscription_set.count()>0:
                        panier = self.client.get_panier()
                        panier.save()
                        panier.copy(self)
                commande_changes_status.send(sender=self.__class__, commande=self, timestamp=timezone.now())

    def delete(self, using=None):
        adresse_fact = self.adresse_fact
        try:
            adresse_fact.delete()
        except:
            pass
        adresse_livr = self.adresse_livr
        try:
            adresse_livr.delete()
        except:
            pass
        for history in self.commandehistory_set.all():
            history.delete()
        super(Commande, self).delete(using=None)

    def existe(self):
        if self.id:
            return True
        return False

    def CheckWithPaylineIfCommandIsPaid(self):
        payline_wsdl_url = finders.find('payline/payline_v4.38.wsdl')
        client = Client(url='file://' + payline_wsdl_url)
        client.set_options(
            location=settings.PAYLINE_URL,
            username=settings.PAYLINE_MERCHANT_ID,
            password=settings.PAYLINE_ACCESS_KEY)
        payline_xml_url = finders.find('payline/payline_getWebPaymentDetailsRequest.xml')
        xml_request = open(payline_xml_url, 'rb').read()
        xml_request = xml_request \
            .replace('REPLACEME_token', str(self.payline_token))
        result = client.service.getWebPaymentDetails(__inject={'msg': xml_request})
        logger.debug("result getWebPaymentDetails : " + str(result))
        statut_paiement = {
            '00000': self.PAYLINE_PAIEMENT_ACCEPTE,
            '01001': self.PAYLINE_PAIEMENT_ACCEPTE,
            '02000': self.PAYLINE_PAIEMENT_PENDING,
            '02101': self.PAYLINE_PAIEMENT_PENDING,
            '02103': self.PAYLINE_PAIEMENT_PENDING,
            '02105': self.PAYLINE_PAIEMENT_PENDING,
            '02109': self.PAYLINE_PAIEMENT_ARRETE,
            '02306': self.PAYLINE_PAIEMENT_PENDING,
            '02319': self.PAYLINE_PAIEMENT_ARRETE,
        }.get(result.result.code, self.PAYLINE_PAIEMENT_REFUSE)
        return statut_paiement, result

    def UpdatePaylineStatus(self):
        statut_paiement, result = self.CheckWithPaylineIfCommandIsPaid()

        if statut_paiement == self.PAYLINE_PAIEMENT_ACCEPTE:
            self.payer(result.transaction.id)
            #Verifier que le mail n'est envoyé qu'une seule fois au client
            if not self.mail_paye_envoye:
                subject = _("Votre commande a bien ete prise en compte")
                to = [self.client.email]
                ctx={
                        'object': self,
                }

                message = get_template('mails/confirmation_commande.html').render(Context(ctx))
                msg = EmailMessage(subject, message, to=to)
                msg.content_subtype = 'html'
                msg.send()
                self.mail_paye_envoye = True
                self.save()
            return

        elif statut_paiement == self.PAYLINE_PAIEMENT_ARRETE:
            # panierCourant = Commande.objects.getUserPanier(self.request)
            self.annuler()
            return

        elif statut_paiement == self.PAYLINE_PAIEMENT_REFUSE:
            # panierCourant = Commande.objects.filter(client=self.request.user,etat='VAL').last()
            self.refuser()
            return

        elif statut_paiement == self.PAYLINE_PAIEMENT_PENDING:
            # panierCourant = Commande.objects.filter(client=self.request.user,etat='VAL').last()
            self.pending()
            return

class CommandeHistory(models.Model):
    commande = models.ForeignKey(Commande)
    date = models.DateTimeField(blank=True, null=True,db_index=True)
    etat = models.CharField(max_length=3, choices=Commande.ETAT_COMMANDES, default='TMP')

    def __unicode__(self):
        return u'historique'+ unicode(self.date) + unicode(self.commande)


class Tag(models.Model):
    text = models.CharField(max_length=255, unique=True)
    def __unicode__(self):
        return self.text

class Livre(models.Model):
    auteurs = models.ManyToManyField(BiblioUser)
    # Translators: PHASES de Livre
    PHASES = (
        # projet en creation par l'utilisateur
        ('CREATION', _('in creation')),
        # projet cree, l'utilisateur a demandé la validation de son projet par la team. Projet non editable par l'auteur
        ('FROZEN', _('creation en attende de validation Bibliocratie')),
        # projet valide par l'equipe bibliocratie
        ('VALIDATE', _('creation validee par Bibliocratie. En attente du CRON')),
        # projet valide en pre-souscription, modifie par le cron. Etat modifiable par l'auteur
        ('FEEDBACK', _('feedback time')),

        # Fin de pres-souscription modifie par cron. Etat modifiable par l'auteur
        ('CREA-FEE', _('last modifications before souscription')),
        # La presouscription est transformée en souscription, elle est toujours éditable
        ('CREATRAN', _('presouscription transformee')),
        # L'auteur reclame la validation de ses changments par l'equipe avant souscription
        ('FROZ-FEE', _('in review from bibliocratie before campaign')),
        # l'equipe valide les modifications et prepare la souscription en attente du CRON
        ('VAL-FEED', _('pre-souscription transformee validee par Bibliocratie. En attente du CRON')),

        ('GETMONEY', _('En cours')),
        # souscription time is over. people gave enough money.
        ('SUCCES', _('Succes')),
        # souscription time is over. time to make new friends and new familly.
        ('ECHEC', _('Echecs')),
        # REVIEW -> CANCELLED : project = porn / spam / ...
        ('CANCELLE', _('annule car pour ou autre'))
    )
    phase = models.CharField(max_length=8, choices=PHASES, default="CREATION",db_index=True)
    TYPE_CATEGORY = (
        ('', _('Categorie')),
        ('ACTU', _('Actu, Politique et Societe')),
        ('ADOLESCE', _('Adolescents')),
        ('ART', _('Art, Musique et Cinema')),
        ('BD', _('Bandes-dessinees')),
        ('BEAU', _('Beaux livres')),
        ('CUISINE', _('Cuisine et Vins')),
        ('DICT', _('Dictionnaires, langues et encyclopedies')),
        ('DROIT', _('Droit')),
        ('ENTREPRI', _('Economie et entreprise')),
        ('EROTISME', _('Erotisme')),
        ('ESOTERIS', _('Esoterisme et Paranormal')),
        ('ETUDE', _('Etudes superieures')),
        ('FAMILLE', _('Bien-etre')),
        ('FANTAISI', _('Fantaisie et Terreur')),
        ('HISTOIRE', _('Histoire')),
        ('HUMOUR', _('Humour')),
        ('INFORMAT', _('Informatique et Internet')),
        ('LITTERAT', _('Litterature')),
        ('SENTIMEN', _('Litterature sentimentale')),
        ('ENFANT', _('Jeunesse')),
        ('LOISIRS', _('Loisirs creatifs, decoration et bricolage')),
        ('MANGA', _('Manga')),
        ('NATURE', _('Nature et animaux')),
        ('PHOTO', _('Photographie')),
        ('POLICIER', _('Policier et Suspense')),
        ('RELIGION', _('Religions et Spiritualites')),
        ('SCIENCEF', _('Science-Fiction')),
        ('SCIENCEH', _('Sciences humaines')),
        ('SCIENCET', _('Sciences, Techniques et Medecine')),
        ('SCOLAIRE', _('Scolaire et Parascolaire')),
        ('SPORT', _('Sports et passions')),
        ('TOURISME', _('Tourisme et Voyages')),
    )
    category = models.CharField(max_length=8, choices=TYPE_CATEGORY, blank=True, default='',db_index=True)
    TYPE_GENRE = (
        ('', _('Genre')),
        ('ALBUM', _('Album')),
        ('CONTES', _('Contes')),
        ('ROMAN', _('Roman')),
        ('ART', _('Art')),
        ('NOUVELLE', _('Nouvelles')),
        ('ESSAI', _('Essai')),
        ('BD', _('Bd')),
        ('CARNETS', _('Carnets de voyage')),
        ('POESIE', _('Poesie')),
        ('THEATRE', _('Theatre')),
    )
    genre = models.CharField(max_length=8, choices=TYPE_GENRE, blank=True, default='',db_index=True)
    TYPE_ETAT = (
        ('', _('Etat')),
        ('NOUVEAU', _('Nouveau')),
        ('POPULAIR', _('Populaire')),
        ('QUASI', _('Quasi')),
        ('SUCCES', _('Succes')),
    )
    is_active = models.BooleanField(default=True)
    etat = models.CharField(max_length=8, choices=TYPE_ETAT, blank=True, default='',db_index=True)
    a_la_une = models.BooleanField(default=False)
    pre_souscription = models.BooleanField(default=True)
    maquette = models.BooleanField(verbose_name=_('La maquette est realisee par Bibliocratie'),default=True)
    contenu_explicite = models.BooleanField(verbose_name=_('Le livre contient du contenu sexuellement explicite'), default=False)
    instructions_maquette = models.TextField(blank=True)
    couverture = models.BooleanField(verbose_name=_('La couverture est realisee par Bibliocratie'),default=True)
    tags = models.ManyToManyField(Tag,blank=True)

    # Starting dates of each phase.
    date_creation = models.DateTimeField(default=timezone.now)
    date_demande_validation_presouscription = models.DateTimeField(verbose_name=_('Date de demande de validation presouscription'),blank=True, null=True)
    date_validation_presouscription = models.DateTimeField(verbose_name=_('Date de validation presouscription'),blank=True, null=True)
    date_demande_validation_souscription = models.DateTimeField(verbose_name=_('Date de demande de validation souscription'),blank=True, null=True)
    date_validation_souscription = models.DateTimeField(verbose_name=_('Date de validation souscription'),blank=True, null=True)
    date_feedback = models.DateTimeField(verbose_name=_('Date de presouscription prevue'),blank=True, null=True)
    date_feedback_cron = models.DateTimeField(verbose_name=_('Date de presouscription effective'),blank=True, null=True)

    date_fin_presouscription = models.DateTimeField(verbose_name=_('Date de fin de presouscription'),blank=True, null=True)
    date_souscription = models.DateTimeField(verbose_name=_('Date de souscription prevue'), blank=True, null=True, db_index=True)
    date_souscription_cron = models.DateTimeField(verbose_name=_('Date de souscription effective'), blank=True, null=True)
    date_closed = models.DateTimeField(verbose_name=_('Date de fin de souscription effective'), blank=True, null=True)
    date_relance_auteur = models.DateTimeField(verbose_name=_('Date de fin de relance de l''auteur pour refaire une souscription'),blank=True, null=True)

    jour5 = models.DateTimeField(verbose_name=_('date d\'envoi du mail 5 jours apres la souscription'), null=True, blank=True,default=None)
    jour20 = models.DateTimeField(verbose_name=_('date d\'envoi du mail 20 jours apres la souscription'), null=True, blank=True,default=None)
    jour30 = models.DateTimeField(verbose_name=_('date d\'envoi du mail mi parcours de la souscription'), null=True, blank=True,default=None)
    five_to_end = models.DateTimeField(verbose_name=_('date d\'envoi du mail 5 jours avant la fin de la souscription'), blank=True,null=True, default=None)
    jour40 = models.DateTimeField(verbose_name=_('date d\'envoi du mail 40 jours apres la fin de la souscription'), blank=True,null=True, default=None)

    pourcentage_souscription_85 = models.DateTimeField(verbose_name=_('date du passage du batch à 85%'), null=True, blank=True, default=None)
    pourcentage_souscription_100 = models.DateTimeField(verbose_name=_('date du passage du batch à 100%'), null=True, blank=True, default=None)
    pourcentage_souscription_200 = models.DateTimeField(verbose_name=_('date du passage du batch à 200%'), null=True, blank=True, default=None)

    # nombre d'exemplaires a partir duquel la souscription est un succes
    nb_exemplaires_cible = models.IntegerField(default=50)
    nb_jours_campagne = models.IntegerField(null=True, blank=True)
    lancement_debut_valide = models.BooleanField(default=False)
    lancement_interieur_valide = models.BooleanField(default=False)
    lancement_couverture_valide = models.BooleanField(default=False)
    lancement_prixdate_valide = models.BooleanField(default=False)
    lancement_vous_valide = models.BooleanField(default=False)
    lancement_fin_valide = models.BooleanField(default=False)
    certif_modification = models.BooleanField(default=False,blank=True)
    certif_proprio = models.BooleanField(default=False,blank=True)
    certif_promo = models.BooleanField(default=False,blank=True)
    certif_exclu = models.BooleanField(default=False,blank=True)
    certif_mineur = models.BooleanField(default=False,blank=True)
    certif_coauteur = models.BooleanField(default=False,blank=True)
    remarques = models.TextField(blank=True)


    titre = models.CharField(max_length=254,db_index=True)
    slug = models.SlugField(_('slug'), max_length=254, blank=True, unique=True, db_index=True)
    # il peut y en avoir plusieurs etant donne qu'ils ne sont pas forcement
    # associes a un compte
    auteur = models.CharField(max_length=254,blank=True)
    biographie = RedactorField(verbose_name=_('Biographie'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True, default="")
    resume = RedactorField(verbose_name=_('Resume'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=True,blank=True, default="")

    pourquoi_ce_livre = RedactorField(verbose_name=_('Pourquoi ce livre'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True, default="")
    phrase_cle = RedactorField(verbose_name=_('Phrase cle'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True, default="")
    annonces = RedactorField(verbose_name=_('Annonces'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True, default="")
    image_couverture = ImageField(verbose_name=_('Image couverture'), upload_to='couvertures',blank=True)
    maquete_couverture = models.FileField(verbose_name=_('Maquete couverture'), upload_to='couvertures',blank=True)

    TYPE_MODELE_COUVERTURE = (
        ('', _('Non choisi')),
        ('C01', _('Modele couleur 1')),
        ('C02', _('Modele couleur 2')),
        ('C03', _('Modele couleur 3')),
        ('C04', _('Modele couleur 4')),
        ('C05', _('Modele couleur 5')),
        ('C06', _('Modele couleur 6')),
        ('C07', _('Modele couleur 7')),
        ('C08', _('Modele couleur 8')),
        ('C09', _('Modele couleur 9')),
        ('C10', _('Modele couleur 10')),
        ('C11', _('Modele couleur 11')),
        ('C12', _('Modele couleur 12')),
        ('N01', _('Modele noir et blanc 1')),
        ('N02', _('Modele noir et blanc 2')),
        ('N03', _('Modele noir et blanc 3')),
        ('N04', _('Modele noir et blanc 4')),
        ('N05', _('Modele noir et blanc 5')),
        ('N06', _('Modele noir et blanc 6')),
        ('N07', _('Modele noir et blanc 7')),
        ('N08', _('Modele noir et blanc 8')),
        ('N09', _('Modele noir et blanc 9')),
        ('N10', _('Modele noir et blanc 10')),
        ('N11', _('Modele noir et blanc 11')),
        ('N12', _('Modele noir et blanc 12')),
    )

    modele_couverture = models.CharField(max_length=3, choices=TYPE_MODELE_COUVERTURE, default='', blank=True)


    fichier_auteur = models.FileField(upload_to="fichiers_auteur", blank=True, null=True)
    fichier_biblio = models.FileField(upload_to="fichiers_biblio", blank=True, null=True)
    TYPE_EXTRAIT = (
        ('I', _('Image')),
        ('T', _('Texte')),
    )
    extrait1_txt = RedactorField(verbose_name=_('Extrait 1'),redactor_options={'lang': 'fr', 'focus': 'true'},
                                 allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    extrait1_img = ImageField(upload_to='extraits',blank=True)
    extrait1_type = models.CharField(max_length=1, choices=TYPE_EXTRAIT, default="T")
    extrait2_txt = RedactorField(verbose_name=_('Extrait 2'),redactor_options={'lang': 'fr', 'focus': 'true'},
                                 allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    extrait2_img = ImageField(upload_to='extraits',blank=True)
    extrait2_type = models.CharField(max_length=1, choices=TYPE_EXTRAIT, default="T")
    extrait3_txt = RedactorField(verbose_name=_('Extrait 3'),redactor_options={'lang': 'fr', 'focus': 'true'},
                                 allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    extrait3_img = ImageField(upload_to='extraits',blank=True)
    extrait3_type = models.CharField(max_length=1, choices=TYPE_EXTRAIT, default="T")
    extrait4_txt = RedactorField(verbose_name=_('Extrait 4'),redactor_options={'lang': 'fr', 'focus': 'true'},
                                 allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    extrait4_img = ImageField(upload_to='extraits',blank=True)
    extrait4_type = models.CharField(max_length=1, choices=TYPE_EXTRAIT, default="T")
    liseuse = models.URLField(blank=True)
    nb_pages = models.PositiveIntegerField(verbose_name=_('Nombre de pages total'),blank=True, null=True)
    nb_pages_couleur = models.PositiveIntegerField(verbose_name=_('Nombre de page couleur'), blank=True, null=True)
    nb_pages_nb = models.PositiveIntegerField(verbose_name=_('Nombre de pages noir & blanc'),blank=True, null=True)
    nb_carac = models.PositiveIntegerField(verbose_name=_('Nombre de caracteres'),blank=True, null=True)
    nb_chapitres = models.PositiveIntegerField(verbose_name=_('Nombre de chapitres'),blank=True, null=True)
    TYPE_FORMAT = (
        ('NTS', _('Not set')),
        ('FM1', _('110x155')),
        ('FM2', _('115x180')),
        ('FM3', _('140x210')),
        ('FM4', _('210x210')),
        ('FM5', _('210x148,5')),
        ('FM6', _('180x240')),
        ('CST', _('Custom')),
    )
    format = models.CharField(max_length=3, choices=TYPE_FORMAT, default='NTS')
    largeur_mm = models.FloatField(default=0., blank=True,null=True)
    hauteur_mm = models.FloatField(default=0., blank=True,null=True)
    prix_vente = models.FloatField(default=0.)
    cout_production = models.FloatField(default=0., blank=True,null=True)
    TYPES_ENCRE = (
        ('', _("Type d'encre")),
        ('NB', _('Noir et Blanc')),
        ('COL', _('Illustration')),
    )
    type_encre = models.CharField(max_length=3, choices=TYPES_ENCRE, blank=True, default='' )


    #SONDAGES
    # on peut pas revenir en arriere dans l'ordre des types ci dessous.
    TYPES = (
        # les gens voient ce qu'il y a d'actuel dans le livre, ils ne peuvent pas voter
        ('NEVER_OPENED', 'jamais ouvert'),
        # les gens peuvent proposer
        ('OPEN', 'ouvert aux propositions'),
        # les gens ne peuvent plus proposer mais ils voient les propositions
        # l'auteur ne pourra plus reouvrir
        ('READ_ONLY', 'ferme aux nouvelles propositions'),
    )
    instructions_titre = RedactorField(verbose_name=_('Instructions pour le choix du titre'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    instructions_prix = RedactorField(verbose_name=_('Instructions pour le choix du prix'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    instructions_couverture = RedactorField(verbose_name=_('Instructions pour le choix de la couverture'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    instructions_extraits = RedactorField(verbose_name=_('Instructions pour le choix des extraits'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    instructions_biographie = RedactorField(verbose_name=_('Instructions pour le choix de la biographie'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True,default="")
    type_titres = models.CharField(max_length=12, choices=TYPES, default='NEVER_OPENED', db_index=True)
    type_prix = models.CharField(max_length=12, choices=TYPES, default='NEVER_OPENED', db_index=True)
    type_couvertures = models.CharField(max_length=12, choices=TYPES, default='NEVER_OPENED', db_index=True)
    type_extraits = models.CharField(max_length=12, choices=TYPES, default='NEVER_OPENED', db_index=True)
    type_biographies = models.CharField(max_length=12, choices=TYPES, default='NEVER_OPENED', db_index=True)

    #lors de la transformation de la presouscription en souscription, permet de savoir si l'utilisateur a fait son choix.
    titre_choisi = models.BooleanField(default=False)
    prix_choisi = models.BooleanField(default=False)
    couverture_choisie = models.BooleanField(default=False)
    biographie_choisie = models.BooleanField(default=False)

    instructions = RedactorField(verbose_name=_('Instructions'),redactor_options={'lang': 'fr', 'focus': 'true'},
                               allow_file_upload=False, allow_image_upload=False,blank=True,default="")

    class meta:
        index_together = ["slug", "is_active"]

    def class_name(self):
        return "Livre"

    def save(self, *args, **kwargs):
        if not self.id:
            #Only set the slug when the object is created.
            try:
                self.slug = slugify(self.titre)
            except:
                i=2
                stop=False
                while not stop:
                    try:
                        self.slug = slugify(self.titre + str(i))
                        stop=True
                    except:
                        i=i+1

        #On sauvegarde la phase de l'objet avant de le sauver
        try:
            ancienne_phase= Livre.objects.get(id=self.id, is_active=True).phase
        except:
            ancienne_phase=None

        super(Livre, self).save(*args, **kwargs)

        #Si l'objet a changé de phase on envoie des signaux
        if ancienne_phase and ancienne_phase!=self.phase:
            livre_changes_phase.send(sender=self.__class__, livre=self, timestamp=timezone.now())
            #Enregistrement de quelques dates cle de la vie du Livre
            if self.phase=='FROZEN':
                if self.pre_souscription:
                    self.date_demande_validation_presouscription=timezone.now()
                else:
                    self.date_demande_validation_souscription=timezone.now()
            elif self.phase=='VALIDATE':
                if self.pre_souscription:
                    self.date_validation_presouscription=timezone.now()
                else:
                    self.date_validation_souscription=timezone.now()
            elif self.phase=="FEEDBACK":
                self.date_feedback_cron=timezone.now()
            elif self.phase=='GETMONEY':
                self.date_souscription_cron=timezone.now()
                self.etat="NOUVEAU"
            elif self.phase=="CREA-FEE":
                self.date_modifs=timezone.now()
            elif self.phase=='VAL-FEED':
                self.date_validation_souscription=timezone.now()
            elif self.phase in ['SUCCES','ECHEC','CANCELLE']:
                self.date_closed=timezone.now()
            super(Livre, self).save(*args, **kwargs)


    def _nb_exemplaires_souscrits(self):
        nb=0
        for souscription in self.souscription_set.filter(etat__in=['ENC','SUC','ECH','REM']):
            nb+= souscription.quantite
        return nb

    nb_exemplaires_souscrits = property(_nb_exemplaires_souscrits)

    def _nb_souscripteurs(self):
        return self.souscription_set.filter(etat__in=['ENC','SUC','ECH','REM']).count()

    nb_souscripteurs = property(_nb_souscripteurs)

    def _nb_demandes_resouscription(self):
        return self.demandernewsouscription_set.count()

    nb_demandes_resouscription = property(_nb_demandes_resouscription)

    def canEditSondage(self):
        return self.phase in ('FB_EDIT', 'REVIEW_F', 'FEEDBACK')

    def get_percent(self):
        if self.nb_exemplaires_cible>0:
            return self.nb_exemplaires_souscrits*100/self.nb_exemplaires_cible
        return 0

    def extrait1_img_url(self):
        dimensions = "250x600"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': False, 'upscale': False, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.extrait1_img, dimensions, **options).url
        except:
            return ""

    def extrait2_img_url(self):
        dimensions = "250x600"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': False, 'upscale': False, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.extrait2_img, dimensions, **options).url
        except:
            return ""

    def extrait3_img_url(self):
        dimensions = "250x600"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': False, 'upscale': False, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.extrait3_img, dimensions, **options).url
        except:
            return ""

    def extrait4_img_url(self):
        dimensions = "250x600"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': False, 'upscale': False, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.extrait4_img, dimensions, **options).url
        except:
            return ""

    def image_50x50_url(self):
        dimensions = "50x50"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': False, 'upscale': False, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.image_couverture, dimensions, **options).url
        except:
            return ""

    def image_300x400_url(self):
        dimensions = "300x400"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': True, 'upscale': True, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.image_couverture, dimensions, **options).url
        except:
            return ""

    def image_is_portrait(self):
        try:
            image_file = default.kvstore.get_or_set(ImageFile(self.image_couverture))
            return image_file.is_portrait()
        except:
            return None

    def image_400x400_url(self):
        if self.image_is_portrait():
            dimensions = "300x400"
        else:
            dimensions = "600x400"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': True, 'upscale': True, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.image_couverture, dimensions, **options).url
        except:
            return ""

    #transforme la presouscription en souscription
    def presouscription_transform(self):
        if self.type_titres!='NEVER_OPENED' and not self.titre_choisi:
            raise Exception("Vous n'avez pas choisi de titre")
        if self.type_prix!='NEVER_OPENED' and not self.prix_choisi:
            raise Exception("Vous n'avez pas choisi de prix")
        if self.type_couvertures!='NEVER_OPENED' and not self.couverture_choisie:
            raise Exception("Vous n'avez pas choisi de couverture")
        if self.type_biographies!='NEVER_OPENED' and not self.biographie_choisie:
            raise Exception("Vous n'avez pas choisi de biographie")
        if self.type_extraits!='NEVER_OPENED' and \
            (TextProposition.objects.filter(livre=self, type='EXTRA',chosen=True).count() + \
             ImageProposition.objects.filter(livre=self,type='EXTRA',chosen=True).count())<4:
            raise Exception("Vous n'avez pas choisi 4 extraits")

        if self.type_titres!='NEVER_OPENED':
            for p in CharProposition.objects.filter(livre=self,chosen=True):
                self.titre = p.valeur
        if self.type_prix!='NEVER_OPENED':
            for p in NumberProposition.objects.filter(livre=self,chosen=True):
                self.prix_vente = p.valeur
        if self.type_couvertures!='NEVER_OPENED':
            for p in ImageProposition.objects.filter(livre=self,type='COVER',chosen=True):
                self.image_couverture = p.valeur
        if self.type_biographies!='NEVER_OPENED':
            for p in TextProposition.objects.filter(livre=self,type='BIO',chosen=True):
                self.couverture = p.valeur
        id_extrait=1
        if self.type_extraits!='NEVER_OPENED':
            for p in TextProposition.objects.filter(livre=self,type='EXTRA',chosen=True):
                if id_extrait==1:
                    self.extrait1_txt = p.valeur
                    self.extrait1_type = 'T'
                elif id_extrait==2:
                    self.extrait2_txt = p.valeur
                    self.extrait2_type = 'T'
                elif id_extrait==3:
                    self.extrait3_txt = p.valeur
                    self.extrait3_type = 'T'
                elif id_extrait==4:
                    self.extrait4_txt = p.valeur
                    self.extrait4_type = 'T'
                id_extrait+=1
            for p in ImageProposition.objects.filter(livre=self,type='EXTRA',chosen=True):
                if id_extrait==1:
                    self.extrait1_img = p.valeur
                    self.extrait1_type = 'I'
                elif id_extrait==2:
                    self.extrait2_img = p.valeur
                    self.extrait2_type = 'I'
                elif id_extrait==3:
                    self.extrait3_img = p.valeur
                    self.extrait3_type = 'I'
                elif id_extrait==4:
                    self.extrait4_img = p.valeur
                    self.extrait4_type = 'I'
                id_extrait+=1
        self.phase='CREATRAN'
        self.save()
        print "presousciption_transform"

    def url(self):
        return reverse('livre_detail', args=[self.slug])
        # return ''.join(['http://', get_current_site(None).domain, reverse('livre_detail', args=[self.slug])])
    url_property = property(url)

    def get_nb_votes(self):
        return Vote.objects.filter(proposition__livre=self).count()

    get_nb_votes_template = property(get_nb_votes)


    def _get_nb_propositions(self):
        return Proposition.objects.filter(livre=self).count()

    get_nb_propositions = property(_get_nb_propositions)

    def get_rating(self):
        try:
            return int(round(self.rating_set.aggregate(Avg('rating'))['rating__avg']))
            votes = self.rating_set.all()
            notes = 0
            poids = 0
            for vote in votes:
                notes += vote.rating * vote.poids
                poids += vote.poids
            return int(round(notes/poids))
        except:
            return 0

    def get_cout_production(self):
        palliers_nb_exemplaires = None
        tarif_fournisseur = None
        try:
            format=self.format
            if format=='NTS':
                raise NotCalculableException("manque le format")

            if format=='CST':
                raise NotCalculableException("non calculable")

            if self.type_encre=='COL':
                if self.nb_pages_nb>10:
                    raise NotCalculableException("non calculable")

            livre=self
            couverture=livre.couverture
            maquette=livre.maquette
            type_encre=livre.type_encre
            tarif_fournisseur = TarifsFournisseur.objects.get(format=format,type_encre=type_encre)
            if self.type_encre=='COL':
                nb_pages=self.nb_pages
            else:
                #Attention, ces formules sont a mettre a jour dans le fichier lancement.js et dans viex ligne 456
                if self.format=='FM1':
                    nb_pages = math.ceil(self.nb_chapitres*0.9+self.nb_carac/860)
                    nb_pages = nb_pages + nb_pages % 2
                elif self.format=='FM2':
                    nb_pages = math.ceil(self.nb_chapitres*1.2+self.nb_carac/1070)
                    nb_pages = nb_pages + nb_pages % 2
                elif self.format=='FM3':
                    nb_pages = math.ceil(self.nb_chapitres*0.7+self.nb_carac/1600)
                    nb_pages = nb_pages + nb_pages % 2

            if nb_pages==0:
                raise NotCalculableException("manque le nombre de pages")
            stop = False
            index = 0
            #trouver la ligne tarrifaire correspondant au nombre de pages
            while not stop:
                try:
                    pallier_nb_pages = tarif_fournisseur.tarifs_impression[index]['pages']
                except IndexError:
                    stop = True
                    index-=1
                    raise NotCalculableException("nombre de pages trop élevé")
                if pallier_nb_pages>=nb_pages:
                    stop = True
                if not stop:
                    index +=1
            ligne_tarifaire = tarif_fournisseur.tarifs_impression[index]
            #trier les palliers de nombre d'exemplaires
            palliers_nb_exemplaires = []
            for key in ligne_tarifaire.keys():
                try:
                    palliers_nb_exemplaires.append(int(key))
                except ValueError:
                    pass
            stop = False
            prix = None
            nb_exemplaires_cible=self.nb_exemplaires_cible
            if nb_exemplaires_cible==0:
                raise NotCalculableException("manque le nombre d'exemplaires cible")
            #trouver le prix
            for pallier in sorted(palliers_nb_exemplaires):
                if pallier>=nb_exemplaires_cible:
                    prix=ligne_tarifaire["%i" % pallier]
                    break
            if not prix:
                raise NotCalculableException("nombre d'exemplaires trop eleve")
            prix_fournisseur = prix

            poids=ligne_tarifaire["poids"]
            #poids = poids d'un bouquin en grammes
            poids_total = float(poids) * nb_exemplaires_cible /1000
            #poids = poids de la livraison en Kg
            stop = False
            index = 0
            #trouver la ligne tarrifaire correspondant au poids
            while not stop:
                try:
                    pallier_kg = tarif_fournisseur.tarifs_expedition[index]['poids']
                except IndexError:
                    stop = True
                    index-=1
                    raise NotCalculableException("poids fournisseur trop élevé")
                if pallier_kg>=poids_total:
                    stop = True
                if not stop:
                    index +=1
            prix_expedition = float(str(tarif_fournisseur.tarifs_expedition[index-1]['tarif']).replace(',','.'))
            #prix de l'expedition Bibliocratie
            tarif_expedition = TarifsExpedition.objects.all().first()
            stop = False
            index = 0
            #trouver la ligne tarrifaire correspondant au poids
            while not stop:
                try:
                    pallier_g = tarif_expedition.tarifs[index]['poids']
                except IndexError:
                    stop = True
                    index-=1
                    raise NotCalculableException("poids bibliocratie trop élevé")
                if pallier_g>=poids:
                    stop = True
                if not stop:
                    index +=1
            prix_expedition_bouquin = float(str(tarif_expedition.tarifs[index-1]['tarif']).replace(',','.'))
            prix_enveloppe_bouquin = float(str(tarif_expedition.tarifs[index-1]['frais']).replace(',','.'))
            prix_expedition_bibliocratie = (prix_expedition_bouquin+prix_enveloppe_bouquin)*nb_exemplaires_cible
            prix_mise_en_page = (0.85 if maquette else 0)* nb_pages
            prix_couverture = 85 if couverture else 0
            prix_fournisseur_ttc = (prix_fournisseur + prix_expedition) * 1.055
            sous_total =  prix_fournisseur_ttc + prix_mise_en_page + prix_couverture+prix_expedition_bibliocratie
            sous_total_tva = sous_total * 1.055
            commission = 0.1*sous_total_tva
            total = sous_total_tva + commission
            prix_exemplaire = total / nb_exemplaires_cible
            prix_exemplaire_arrondi = float(math.ceil(prix_exemplaire*10))/10


            out_data = {
                'prix_exemplaire' : prix_exemplaire_arrondi,
                'message' : None
            }
        except NotCalculableException as e:
            out_data = {
                'message' : e.message,
                'prix_exemplaire' : None,
            }
        if not palliers_nb_exemplaires and tarif_fournisseur:
            ligne_tarifaire = tarif_fournisseur.tarifs_impression[0]
            #trier les palliers de nombre d'exemplaires
            palliers_nb_exemplaires = []
            for key in ligne_tarifaire.keys():
                try:
                    palliers_nb_exemplaires.append(int(key))
                except ValueError:
                    pass

        out_data['palliers_nb_exemplaires'] = sorted(palliers_nb_exemplaires) if palliers_nb_exemplaires else [50,60,70,100,120,150,200]

        return out_data



    @property
    def date_fin_souscription_millisecondes(self):
        if self.date_souscription:
            datefin= self.date_souscription + timedelta(days=self.nb_jours_campagne)
            return int((datefin-datetime(1970,1,1,tzinfo=pytz.utc)).total_seconds())*1000
        else:
            return None
            # YYYY/MM/DD hh:mm:ss

    @property
    def souscription_jours_restants(self):
        if self.date_souscription:
            datefin= self.date_souscription + timedelta(days=self.nb_jours_campagne)
            now = timezone.now()
            jours_restant = int((datefin-now).days)
            if jours_restant<0:
                return 0
            return jours_restant
        else:
            return None

    # TODO passer par un tag pour afficher une liste d'auteurs
    @property
    def lib_auteurs(self):
        liste = []
        for element in self.auteurs.all():
            liste.append(str(element))
        return ', '.join(liste)

    @property
    def lib_extrait(self):
        if self.extrait:
            return self.extrait
        else:
            return self.resume

    def __unicode__(self):
        return u'%s' % (self.titre)

class Rating(models.Model):
    user = models.ForeignKey(BiblioUser)
    livre = models.ForeignKey(Livre)
    rating = models.PositiveIntegerField(null=True)
    poids = models.IntegerField(default=1)

    class Meta:
        unique_together = (("user", "livre", 'rating'),)

    def __unicode__(self):
        if self.user.username == 'Anonyme':
            return self.user.username + ' a noté le livre: ' + self.livre.titre + ' -> ' + str(self.poids)
        else:
            return self.user.username + ' a noté le livre: ' + self.livre.titre + ' -> ' + str(self.rating)

class MeRappeler(models.Model):
    user = models.ForeignKey(BiblioUser)
    livre = models.ForeignKey(Livre)

    class Meta:
        unique_together = (("user", "livre"),)

class DemanderNewSouscription(models.Model):
    user = models.ForeignKey(BiblioUser)
    livre = models.ForeignKey(Livre)

    class Meta:
        unique_together = (("user", "livre"),)

class TarifsFournisseur(models.Model):
    tarifs_impression = JSONField(blank=True)
    tarifs_expedition = JSONField(blank=True)
    format = models.CharField(max_length=3, choices=Livre.TYPE_FORMAT, default='')
    type_encre = models.CharField(max_length=3, choices=Livre.TYPES_ENCRE, default='' )
    sheet_key = models.CharField(max_length=44, default='' )
    worksheet_impression = models.CharField(max_length=30, default='' )
    worksheet_expedition = models.CharField(max_length=30, default='' )

    class Meta:
        unique_together = (("format", "type_encre"),)

    def __unicode__(self):
        return u'Tarifs format %s %s' % (self.get_format_display(),self.get_type_encre_display())

class TarifsExpedition(models.Model):
    tarifs = JSONField(blank=True)
    sheet_key = models.CharField(max_length=44, default='' )
    worksheet = models.CharField(max_length=30, default='' )

    def __unicode__(self):
        return u'Tarifs expedition'



class Souscription(models.Model):
    """Quand un panier est en cours, on cree des souscriptions. Une fois le panier
    commande, les souscriptions restent dans la base en attente du succes
    ou non du projet."""
    panier = models.ForeignKey(Commande)
    # Translators: ETAT_SOUSCRIPTIONS de Souscription
    ETAT_SOUSCRIPTIONS = (
        ('TMP', _('Panier')),
        ('ENC', _('En cours')),
        ('SUC', _('Succes')),
        ('ECH', _('Echoue')),
        ('REM', _('Rembourse')),
        ('ANL', _('Annule')),
    )
    etat = models.CharField(max_length=3, choices=ETAT_SOUSCRIPTIONS, db_index=True)
    livre = models.ForeignKey(Livre)
    quantite = models.PositiveIntegerField()
    rang = models.IntegerField(default=0)
    souscription_pourcent = models.IntegerField(default=0)
    merged = models.BooleanField(default=False)

    def __unicode__(self):
        return '%d exemplaires de %s' % (self.quantite, self.livre.titre)

    @property
    def prix(self):
        return self.livre.prix_vente * self.quantite

    def delete(self, using=None):
        for discount in self.panier.discount_set.all():
            discount.delete()
        for history in self.souscriptionhistory_set.all():
            history.delete()
        super(Souscription,self).delete(using)

    def copy(self, souscription):
        self.panier = souscription.panier
        self.etat = souscription.etat
        self.livre = souscription.livre
        self.quantite = souscription.quantite

    def valider(self):
        self.etat = 'ENC'
        self.rang=Souscription.objects.filter(livre=self.livre).exclude(etat='ANL').count()
        self.souscription_pourcent = self.livre.get_percent()
        self.save()

    def expedier(self):
        self.etat = 'EXP'
        self.save()

    def rembourser(self):
        self.etat = 'REM'
        self.save()

    def annuler(self):
        self.etat = 'ANL'
        self.save()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        try:
            ancien_etat= Souscription.objects.get(id=self.id).etat
        except:
            ancien_etat=None
        super(Souscription, self).save(force_insert, force_update, using, update_fields=None)
        if ancien_etat and ancien_etat!=self.etat:
            h = SouscriptionHistory(souscription=self, etat=self.etat)
            h.save()
            souscription_changes_status.send(sender=self.__class__, souscription=self, timestamp=timezone.now())

class SouscriptionHistory(models.Model):
    souscription = models.ForeignKey(Souscription)
    date = models.DateTimeField(blank=True, null=True,default=timezone.now)
    etat = models.CharField(max_length=3, choices=Souscription.ETAT_SOUSCRIPTIONS, default='TMP')

# class Inscription(models.Model):
#     """Quand un panier est en cours, on cree des souscriptions. Une fois le panier
#     commande, les souscriptions restent dans la base en attente du succes
#     ou non du projet."""
#     panier = models.ForeignKey(Commande)
#     # Translators: ETAT_INSCRIPTION de Inscription
#     ETAT_INSCRIPTION = (
#         ('TMP', _('Commande')),
#         ('ENC', _('En cours')),
#         ('EXP', _('Expedie')),
#         ('REM', _('Rembourse')),
#         ('ANL', _('Annule')),
#     )
#     etat = models.CharField(max_length=3, choices=ETAT_INSCRIPTION)
#     # atelier = models.ForeignKey(Atelier)
#     quantite = models.PositiveIntegerField()
#     merged = models.BooleanField(default=False)
#
#
#     def delete(self, using=None):
#         for discount in self.panier.discount_set.all():
#             discount.delete()
#         super(Inscription,self).delete(using)
#
#     def __unicode__(self):
#         return u'%d exemplaires de %s' % (self.quantite, self.livre.atelier)
#
#     def copy(self, inscription):
#         self.panier = inscription.panier
#         self.etat = inscription.etat
#         self.atelier = inscription.atelier
#         self.quantite = inscription.quantite
#
#     def valider(self):
#         self.etat = 'ENC'
#         self.save()
#
#     def expedier(self):
#         self.etat = 'EXP'
#         self.save()
#
#     def rembourser(self):
#         self.etat = 'REM'
#         self.save()
#
#     def annuler(self):
#         self.etat = 'ANL'
#         self.save()

class DiscountCode(models.Model):
    # Translators: PRODUCT_TYPE de DiscountCode
    PRODUCT_TYPE = (
        ('LIV', _('Livre')),
        ('ATE', _('Atelier')),
        ('ALL', _('Tout')),
    )
    # Translators: DISCOUNT_TYPE de DiscountCode
    DISCOUNT_TYPE = (
        ('PER', _('Pourcent')),
        ('RED', _('Reduction')),
    )
    code = models.CharField(max_length=10, db_index=True)
    date_start = models.DateTimeField(default=timezone.now)
    date_end = models.DateTimeField(default=timezone.now)
    # Ce code indique combien de fois le code peut etre utilise.
    quantity = models.IntegerField(default=0)

    # type de produit
    product_type = models.CharField(max_length=3, choices=PRODUCT_TYPE, default='ALL')
    # Cle renseignee si le produit est un livre
    livre = models.ForeignKey(Livre, blank=True, null=True, default=None)
    # Cle renseignee si le produit est un atelier
    # atelier = models.ForeignKey(Atelier, blank=True, null=True, default=None)

    # Cle renseignee si la discount a lieu sur un livre
    livre = models.ForeignKey(Livre, blank=True, null=True, default=None)

    #type de reduction % ou €
    discount_type = models.CharField(max_length=3, choices=DISCOUNT_TYPE)
    # Valeur renseignee si la discount est une reduction en euro
    discount_reduction = models.FloatField(blank=True, null=True)
    # Valeur renseignee si la discount est une reduction en pourcentage
    discount_percent = models.FloatField(blank=True,null=True)

    def get_reduction(self, panier):
        reduc=0
        if self.product_type=="LIV":
            #la discount est sur un livre
            for souscription in panier.souscription_set.all():
                if souscription.livre==self.livre:
                    if self.discount_type=='RED':
                        return -self.discount_reduction
                    if self.discount_type=="PER":
                        return -souscription.prix*self.discount_percent/100
            #aucun livre ne correspond a la discount
            raise Exception(_("Aucun livre dans le panier ne correspond a la Discount"))
        if self.product_type=='ATE':
            #la discount est sur un atelier
            for atelier in panier.atelier_set.all():
                if atelier==self.atelier:
                    if self.discount_type=='RED':
                        return -self.discount_reduction
                    if self.discount_type=="PER":
                        return -atelier.prix*self.discount_percent/100
            #aucun livre ne correspond a la discount
            raise Exception(_("Aucun atelier dans le panier ne correspond a la Discount"))
        if self.product_type=='ALL':
            #la discount est sur l'ensemble du panier
            if self.discount_type=='RED':
                return -self.discount_reduction
            prix_panier=panier.total_sans_discount_ni_taxes
            if self.discount_type=="PER":
                return -prix_panier*self.discount_percent/100


    def __unicode__(self):
        if self.product_type=='LIV':
            if self.discount_type=='PER':
                return u'%s : %.2f%% de reduction sur le livre %s' % (self.code, self.discount_percent, self.livre.titre)
            elif self.discount_type=='RED':
                return u'%s : %.2f€ de reduction sur le livre %s' % (self.code, self.discount_reduction, self.livre.titre)
        if self.product_type=='ATE':
            if self.discount_type=='PER':
                return u'%s : %.2f%% de reduction sur l''atelier %s' % (self.code, self.discount_percent, self.atelier.titre)
            elif self.discount_type=='RED':
                return u'%s : %.2f€ de reduction sur l''atelier %s' % (self.code, self.discount_reduction, self.atelier.titre)
        if self.product_type=='ALL':
            if self.discount_type=='PER':
                return u'%s : %.2f%% de reduction sur le panier' % (self.code, self.discount_percent)
            elif self.discount_type=='RED':
                return u'%s : %.2f€ de reduction sur le panier' % (self.code, self.discount_reduction)



class Discount(models.Model):
    panier = models.ForeignKey(Commande)
    discount = models.ForeignKey(DiscountCode)

    def __init__(self, *args, **kwargs):
        super(Discount,self).__init__(*args, **kwargs)

    def get_reduction(self):
        return self.discount.get_reduction(self.panier)


class Proposition(models.Model):
    auteur = models.ForeignKey(BiblioUser)
    livre = models.ForeignKey(Livre)
    date_creation = models.DateTimeField(default=timezone.now)
    #quand l'auteur choisit une proposition, les autres ne sont plus visibles par lui -> deleted = True
    deleted = models.BooleanField(default=False)
    #quand l'auteur déicde de ne pas choisir une proposition, il en fait une qui est choisie celle ci n'est visible que par lui -> private = True
    private = models.BooleanField(default=False)
    #Quand l'auteur choisit une proposition
    chosen = models.BooleanField(default=False)

    def getTypedProposition(self):
        try:
            proposition = self.charproposition
        except:
            try:
                proposition = self.numberproposition
            except:
                try:
                    proposition = self.imageproposition
                except:
                    try:
                        proposition = self.textproposition
                    except:
                        proposition = None
        return proposition

    def choisir(self):
        #fonction appelée par l'auteur quand la presouscription se transforme en souscription

        livre = self.livre
        type = self.get_type()
        if type == 'TITRE':
            livre.titre_choisi=True
            livre.save()
            for p in CharProposition.objects.filter(livre=livre):
                if p==self:
                    p.chosen=True
                    p.save()
                else:
                    if not p.deleted:
                        p.deleted=True
                        p.chosen=False
                        p.save()
        elif type in ['EXTRA']:
            if self.chosen:
                self.chosen = False
                self.save()
                return
            count = TextProposition.objects.filter(livre=livre,type='EXTRA',chosen=True).count() + ImageProposition.objects.filter(livre=livre,type='EXTRA',chosen=True).count()
            if count<4:
                self.chosen = True
                self.save()
            else:
                raise Exception("Vous ne pouvez pas selectionner plus de 4 propositions")
        elif type in ['BIO']:
            livre.biographie_choisie =True
            livre.save()
            for p in TextProposition.objects.filter(livre=livre):
                if p==self:
                    p.chosen=True
                    p.save()
                else:
                    if not p.deleted:
                        p.deleted=True
                        p.chosen=False
                        p.save()

        elif type == 'NUMBER':
            livre.prix_choisi =True
            livre.save()
            for p in NumberProposition.objects.filter(livre=livre):
                if p==self:
                    p.chosen=True
                    p.save()
                else:
                    if not p.deleted:
                        p.deleted=True
                        p.chosen=False
                        p.save()
        elif type == 'COVER':
            livre.couverture_choisie =True
            livre.save()
            for p in ImageProposition.objects.filter(livre=livre,type='COVER'):
                if p==self:
                    p.chosen=True
                    p.save()
                else:
                    if not p.deleted:
                        p.deleted=True
                        p.chosen=False
                        p.save()


class Vote(models.Model):
    user = models.ForeignKey(BiblioUser)
    proposition = models.ForeignKey(Proposition)
    class Meta:
        unique_together = (("user", "proposition"),)

class CharProposition(Proposition):
    valeur = models.CharField(max_length=50, blank=True)

    def get_type(self):
        return 'TITRE'

class TextProposition(Proposition):
    TYPES = (
        ('EXTRA', 'extrait'),
        ('BIO', 'biographie'),
    )
    type = models.CharField(max_length=6, choices=TYPES)
    valeur = models.TextField(blank=True)

    def get_type(self):
        return self.type


class NumberProposition(Proposition):
    valeur = models.FloatField(default=0)

    def get_type(self):
        return 'NUMBER'

class ImageProposition(Proposition):
    TYPES = (
        ('EXTRA', 'extrait'),
        ('COVER', 'Couverture'),
    )
    type = models.CharField(max_length=6, choices=TYPES)
    valeur = ImageField(upload_to='sondages',blank=True)

    def get_type(self):
        return self.type

    def image_260x260(self):
        dimensions = "260x260"
        options = {'rounded': None, 'padding_color': '#ffffff', 'format': u'JPEG', 'colorspace': 'RGB', 'cropbox': None, 'padding': False, 'upscale': False, 'crop': 'center', 'image_info': {'jfif_version': (1, 1), 'jfif': 257, 'jfif_unit': 0, 'jfif_density': (1, 1)}, 'quality': 95}
        try:
            return get_thumbnail(self.valeur, dimensions, **options).url
        except:
            return ""



class Commentaire(models.Model):
    user = models.ForeignKey(BiblioUser)
    avis_lecture = models.BooleanField(default=False)
    contenu = models.CharField(max_length=2000)
    date = models.DateTimeField(default=timezone.now)
    livre = models.ForeignKey(Livre, blank=True)
    reponse_a = models.ForeignKey("self",blank=True,null=True)
    def __unicode__(self):
        return self.contenu

class UrlIndex(models.Model):
    url = models.URLField()
    texte = models.TextField()
    image = models.ImageField(default=None, blank=True)
    titre = models.CharField(max_length=80,default=None)

    def class_name(self):
        return 'UrlIndex'

    def image_url(self):
        try:
            return ''.join(['http://', get_current_site(None).domain, self.image.url])
        except:
            pass

    def __unicode__(self):
        return self.titre


# class Prof(models.Model):
#     models.ForeignKey(BiblioUser)
#     video_prof = EmbedVideoField()
#     video_createur = EmbedVideoField()
#     nom_animateur = models.CharField(max_length=255)
#     prof_prenom = models.CharField(max_length=255)
#     prof_nom = models.CharField(max_length=255)
#     prof_bio = models.TextField()
#     prof_illustration = models.ImageField()
#     prof_bio_reduc = models.TextField()
#     prof_profil = models.URLField()
#     prof_site = models.URLField()
#
# class MediaType(models.Model):
#     media_type = models.CharField(max_length=20)
#
# class Atelier(models.Model):
#     ATELIER_TYPE = (
#         ('GENRELIT', _('Genre litteraire')),
#         ('TECHNIC', _('Technique')),
#     )
#     titre = models.CharField(max_length=255)
#     sous_titre = models.CharField(max_length=255)
#     prof = models.ForeignKey(Prof)
#     type = models.CharField(max_length=8, choices=ATELIER_TYPE )
#     illustration = ImageField(upload_to="ateliers")
#     ATELIER_OPTION = (
#         ('GROUPE', _('En groupe')),
#         ('SOLO', _('Solo')),
#     )
#     option = models.CharField(max_length=8, choices=ATELIER_OPTION )
#     txt_presentation = models.TextField(default="")
#     txt_presentation_reduit = models.TextField(default="")
#     #duree en mois de l'atelier
#     duree_session_groupe = TimedeltaField()
#     #temps moyen par semaine a consacrer a l'atelier
#     TEMPS_HEBDO = (
#         ('30A1', _('30 minutes a 1 heure')),
#         ('1A2', _('1 a 2 heures')),
#         ('1A3', _('1 a 3 heures')),
#         ('2A4', _('2 a 4 heures')),
#         ('4A6', _('4 a 6 heures')),
#         ('6A10', _('6 a 10 heures')),
#         ('10A15', _('10 a 15 heures')),
#     )
#     temps_hebdo = models.CharField(max_length=8, choices=TEMPS_HEBDO )
#     #temps imparti pour les eleves pour rendre leurs propositions
#     delai_reponse_proposition = TimedeltaField(default='7 days', blank=True, null=True)
#     #temps necessaire a la correction
#     delai_attente_retour = TimedeltaField(default='5 days', blank=True, null=True)
#     #l'atelier contient-il une methode
#     bool_methode_ecriture = models.BooleanField(default=False)
#     #
#     methode_ecriture = models.FileField(upload_to="methodes", blank=True, null=True)
#     TYPE_OFFRE = (
#         ('BRZ', _('Bronze')),
#         ('SILV', _('Argent')),
#         ('GOLD', _('Or')),
#         ('PLAT', _('Platinum')),
#         ('ALL', _('Toutes')),
#     )
#     accessible_offre = models.CharField(max_length=8, choices=TYPE_OFFRE, default='ALL' )
#     prix = models.FloatField()
#     #niveau requis pour les participants:
#     # 'Tout le monde'),
#     # 'Vous avez deja participe a un atelier d''ecriture'),
#     # 'Vous devez avoir participe a l''atelier'),
#     niveau_requis = models.CharField(max_length=255)
#     type_media_present = models.ManyToManyField(MediaType)
#     teaser = EmbedVideoField()
#
# class SessionAtelier(models.Model):
#     atelier = models.ForeignKey(Atelier)
#     date_start = models.DateTimeField()
#     user = models.ManyToManyField(BiblioUser)
#
# class CommentaireAtelier:
#     user = models.ForeignKey(BiblioUser)
#     atelier = models.ForeignKey(Atelier)
#     commentaire = models.TextField
#
# class Bilan(models.Model):
#     atelier = models.ForeignKey(Atelier)
#     txt_presentation = models.TextField()
#     etherpad = models.ForeignKey(Pad)
#
# class Module(models.Model):
#     atelier = models.ForeignKey(Atelier)
#     titre = models.CharField(max_length=255)
#     illustration = models.ImageField()
#     text_presentation_video = models.TextField()
#     text_objectif = models.TextField()
#     video_principale = EmbedVideoField()
#     titre_proposition = models.CharField(max_length=255)
#     lien_etherpad = models.ForeignKey(Pad)
#     titre_complementaire = models.CharField(max_length=255)
#     txt_presentation_complementaire = models.TextField()
#     illustration_complementaire = models.ImageField()
#     date_parution_module = models.DateTimeField(blank=True, null=True)
#     # contenu_complementaire = ?????????????
#
# class Projet(models.Model):
#     txt_method = models.CharField(max_length=255)
#     titre_methode_projet = models.CharField(max_length=255)
#     txt_method_projet = models.TextField()
#     illustration = models.ImageField()
#     lien_etherpad = models.ForeignKey(Pad)
#
# class Transaction(models.Model):
#     """A tout echange d'argent effectue avec succes une transaction est creee.
#     Ce peut etre :
#     _ associe a un panier (achat ou remboursement d'un ancien achat),
#       paye ou rembourse sur par avoir.
#     _ associe a un panier (idem), paye ou rembourse via l'interface payline
#     _ argent direct (ex: on paye l'auteur sur l'argent gagne ; il n'a pas de panier)
#     """
#     ETAT = (
#         ('AVOIR', _('credit ou debit d\'avoir')),
#         ('PAYLINE', _('achat ou remboursement d\'un achat sur payline')),
#         ('DIRECT', _('quand on ne peut pas rembourser autrement, virement direct (via payline aussi)')),
#     )
#     type = models.CharField(max_length=7, choices=ETAT)
#     # Uniquement si mode=AVOIR ou PAYLINE
#     panier = models.ForeignKey(Commande, blank=True)
#     # Uniquement si mode=DIRECT
#     user = models.ForeignKey(BiblioUser, blank=True)
#     # si > 0 : argent du client -> bibliocratie. paiement
#     # si < 0 : argent de bibliocratie -> client. remboursement
#     montant = models.IntegerField()
#     date = models.DateTimeField(default=timezone.now)
#     # si type=DIRECT, ça se passe "au telephone" pour un remboursement,
#     # le client donne son numero de carte. on enregistre les 4 derniers chiffres
#     #  histoire d'avoir une trace mais anonyme quand meme'.
#     credit_card_number = models.CharField(max_length=4)
#     # valable pour types PAYLINE et AVOIR
#     payline_token = models.CharField(max_length=50, blank=True)
