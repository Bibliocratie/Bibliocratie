from rest_framework import serializers
from django_countries import countries
from django.utils.encoding import force_text

from bibliocratie.models import *
from bibliocratie.templatetags.bibliotags import daysuntil
from django.db.models import Q


class MiniUserSerializer(serializers.ModelSerializer):
    thumbnail_50x50 = serializers.SerializerMethodField()
    nom = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    auteur = serializers.SerializerMethodField()

    class Meta:
        model = BiblioUser
        fields = ('nom','thumbnail_50x50','url', 'slug', 'auteur')

    def get_nom(self,obj):
        return obj.display_name()

    def get_thumbnail_50x50(self,obj):
        return obj.avatar_50x50_url()

    def get_url(self,obj):
        return obj.profil_url()

    def get_auteur(self,obj):
        return obj.livre_set.count()>0

class LivreMiniSerializer(serializers.ModelSerializer):
    nb_exemplaires_souscrits  = serializers.SerializerMethodField()
    nb_souscripteurs = serializers.SerializerMethodField()
    percent = serializers.SerializerMethodField()
    thumbnail_50x50 = serializers.SerializerMethodField()
    thumbnail_400x400 = serializers.SerializerMethodField()
    derniers_souscripteurs = serializers.SerializerMethodField()
    resume = serializers.SerializerMethodField()
    class Meta:
        model = Livre
        fields = ('id','url','nb_exemplaires_souscrits','nb_souscripteurs','nb_exemplaires_cible', 'percent','phase',
                  'date_fin_souscription_millisecondes', 'titre','auteur','thumbnail_400x400','thumbnail_50x50','derniers_souscripteurs','resume')

    def get_nb_exemplaires_souscrits(self, obj):
        return obj.nb_exemplaires_souscrits

    def get_nb_souscripteurs(self,obj):
        return obj.nb_souscripteurs

    def get_percent(self,obj):
        if obj.nb_exemplaires_cible>0:
            return obj.nb_exemplaires_souscrits*100/obj.nb_exemplaires_cible

    def get_thumbnail_400x400(self,obj):
        return obj.image_400x400_url()

    def get_thumbnail_50x50(self,obj):
        return obj.image_50x50_url()

    def get_derniers_souscripteurs(self,obj):
        last_souscripteurs=BiblioUser.objects.filter(
                                                     commande__souscription__etat__in=['ENC','SUC','ECH','REM'],
                                                     commande__souscription__livre=obj,
                                                     commande__etat='PAY',
                                                     is_active=True).order_by('-commande__souscription__id')[:3]
        return MiniUserSerializer(last_souscripteurs,many=True).data

    def resume(self,obj):
        return obj.resume

class AdresseSerializer(serializers.ModelSerializer):
    pays = serializers.SerializerMethodField()
    class Meta:
        model = Adresse
        fields = ('nom','prenom','adresse','complement_adresse','code_postal','ville','pays', 'phone')

    def get_pays(self,obj):
        return force_text(obj.pays)

class BiblioUserSerializer(serializers.ModelSerializer):
    thumbnail_50x50 = serializers.SerializerMethodField()
    thumbnail_200x200 = serializers.SerializerMethodField()
    nom = serializers.SerializerMethodField()
    nb_followers = serializers.SerializerMethodField()
    nb_following = serializers.SerializerMethodField()
    nb_livres_suivis = serializers.SerializerMethodField()
    mes_livres = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    auteur = serializers.SerializerMethodField()

    class Meta:
        model = BiblioUser
        fields = ('id', 'nom','thumbnail_50x50','thumbnail_200x200','nb_followers','nb_following','nb_livres_suivis','url',
                  'slug','auteur','mes_livres', 'biographie')

    def get_nom(self,obj):
        return obj.display_name()

    def get_thumbnail_50x50(self,obj):
        return obj.avatar_50x50_url()

    def get_thumbnail_200x200(self,obj):
        return obj.avatar_200x200_url()

    def get_nb_followers(self,obj):
        return Follow.objects.filter(suit=obj,lien='AMI').count()

    def get_nb_following(self,obj):
        return Follow.objects.filter(qui=obj,lien='AMI').count()

    def get_nb_livres_suivis(self,obj):
        return obj.livres_suivis().count()

    def get_url(self,obj):
        return obj.profil_url()

    def get_mes_livres(self,obj):
        return LivreMiniSerializer(obj.livres_suivis(),many=True).data

    def get_auteur(self,obj):
        return obj.livre_set.count()>0

class BiblioStaffUserSerializer(serializers.ModelSerializer):
    thumbnail_50x50 = serializers.SerializerMethodField()
    nom = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    adresse = AdresseSerializer()

    class Meta:
        model = BiblioUser
        fields = ('id','nom','thumbnail_50x50','url','email','adresse')

    def get_nom(self,obj):
        return obj.display_name()

    def get_thumbnail_50x50(self,obj):
        return obj.avatar_50x50_url()

    def get_url(self,obj):
        return obj.profil_url()



class CommentaireSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()
    reponses = serializers.SerializerMethodField()
    livre = LivreMiniSerializer()
    # ajout 3 champs
    nom = serializers.SerializerMethodField()
    prenom = serializers.SerializerMethodField()
    titre = serializers.SerializerMethodField()

    class Meta:
        model = Commentaire
        fields = ('id','user','contenu','date','livre','reponses','nom','titre','prenom','avis_lecture')

    def get_reponses(self,obj):
        commentaires = Commentaire.objects.filter(reponse_a=obj)
        if commentaires:
            return CommentaireSerializer(commentaires,many=True,context=self.context).data
        return []

        # ajout 3 defs
    def get_nom(self,obj):
        return obj.user.nom

    def get_prenom(self,obj):
        return obj.user.prenom

    def get_titre(self,obj):
        return obj.livre.titre

class SouscriptionApiSerializer(serializers.ModelSerializer):
    api_message_type = serializers.SerializerMethodField()
    thumbnail_300x400 = serializers.SerializerMethodField()
    thumbnail_400x400 = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    percent = serializers.SerializerMethodField()
    is_portrait = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    auteurs = MiniUserSerializer(many=True)
    commentaires = serializers.SerializerMethodField()

    class Meta:
        model = Livre
        fields = ('api_message_type','id','thumbnail_300x400','genre','etat','titre', 'resume','url','percent','is_portrait',
                  'a_la_une','thumbnail_400x400','auteurs','category','category_display','genre','nb_exemplaires_souscrits',
                  'nb_souscripteurs','souscription_jours_restants', 'commentaires')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(SouscriptionApiSerializer, self).__init__(*args, **kwargs)

    def get_api_message_type(self, obj):
        return "LIVRE"

    def get_thumbnail_300x400(self,obj):
        return obj.image_300x400_url()

    def get_url(self, obj):
        return obj.url()

    def get_percent(self,obj):
        return obj.get_percent()

    def get_is_portrait(self,obj):
        return obj.image_is_portrait()

    def get_category_display(self,obj):
        return obj.get_category_display()

    def get_thumbnail_400x400(self,obj):
        return obj.image_400x400_url()

    def get_commentaires(self,obj):
        commentaires = obj.commentaire_set.filter(reponse_a=None)
        if commentaires:
            return CommentaireSerializer(commentaires,many=True,context=self.context).data


class LivreApiSerializer(serializers.ModelSerializer):
    api_message_type = serializers.SerializerMethodField()
    nb_exemplaires_souscrits  = serializers.SerializerMethodField()
    nb_souscripteurs = serializers.SerializerMethodField()
    nb_demandes_resouscription = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    percent = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    thumbnail_50x50 = serializers.SerializerMethodField()
    thumbnail_400x400 = serializers.SerializerMethodField()
    thumbnail_300x400 = serializers.SerializerMethodField()
    date_fin_souscription_millisecondes = serializers.SerializerMethodField()
    commentaires = serializers.SerializerMethodField()
    is_portrait = serializers.SerializerMethodField()
    format = serializers.SerializerMethodField()
    extrait1_img_url = serializers.SerializerMethodField()
    extrait2_img_url = serializers.SerializerMethodField()
    extrait3_img_url = serializers.SerializerMethodField()
    extrait4_img_url = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    derniers_souscripteurs = serializers.SerializerMethodField()
    nb_votes = serializers.SerializerMethodField()
    jours_pour_voter = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()

    class Meta:
        model = Livre
        fields = ('api_message_type','id','url','nb_exemplaires_souscrits','phase','nb_pages','type_encre','contenu_explicite',
                  'nb_souscripteurs','nb_exemplaires_cible', 'percent','timestamp','date_fin_souscription_millisecondes',
                  'titre','auteurs','resume','image_couverture','thumbnail_50x50','thumbnail_400x400','thumbnail_300x400',
                  'category','category_display','genre','etat','prix_vente','commentaires','is_portrait','a_la_une','format','nb_votes','jours_pour_voter',
                  'extrait1_type','extrait1_txt','extrait1_img_url',
                  'extrait2_type','extrait2_txt','extrait2_img_url',
                  'extrait3_type','extrait3_txt','extrait3_img_url',
                  'extrait4_type','extrait4_txt','extrait4_img_url',
                  'type_titres','type_prix','type_couvertures','rating',
                  'titre_choisi','prix_choisi','couverture_choisie','biographie_choisie','nb_demandes_resouscription',
                  'type_extraits','type_biographies','maquette','couverture','derniers_souscripteurs','slug'
        )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(LivreApiSerializer, self).__init__(*args, **kwargs)

    def get_rating(self,obj):
        return obj.get_rating()

    def get_derniers_souscripteurs(self,obj):
        last_souscripteurs=BiblioUser.objects.filter(commande__souscription__livre=obj,
                                                     commande__souscription__etat='ENC',
                                                     commande__etat='PAY',
                                                     is_active=True).order_by('-commande__souscription__id')[:3]
        return MiniUserSerializer(last_souscripteurs,many=True).data

    def get_category_display(self,obj):
        return obj.get_category_display()

    def get_extrait1_img_url(self,obj):
        return obj.extrait1_img_url()

    def get_extrait2_img_url(self,obj):
        return obj.extrait2_img_url()

    def get_extrait3_img_url(self,obj):
        return obj.extrait3_img_url()

    def get_extrait4_img_url(self,obj):
        return obj.extrait4_img_url()

    def get_commentaires(self,obj):
        commentaires = obj.commentaire_set.filter(reponse_a=None)
        if commentaires:
            return CommentaireSerializer(commentaires,many=True,context=self.context).data

    def get_format(self,obj):
        return obj.get_format_display()

    def get_api_message_type(self, obj):
        return "LIVRE"

    def get_nb_exemplaires_souscrits(self, obj):
        return obj.nb_exemplaires_souscrits

    def get_nb_souscripteurs(self,obj):
        return obj.nb_souscripteurs

    def get_nb_demandes_resouscription(self,obj):
        return obj.nb_demandes_resouscription

    def get_nb_votes(self,obj):
        return obj.get_nb_votes()

    def get_jours_pour_voter(self,obj):
        if (obj.date_fin_presouscription):
            return daysuntil(obj.date_fin_presouscription)

    def get_timestamp(self,obj):
        return str(timezone.now())

    def get_percent(self,obj):
        return obj.get_percent()

    def get_url(self, obj):
        return obj.url()

    def get_date_fin_souscription_millisecondes(self,obj):
        return obj.date_fin_souscription_millisecondes

    def get_thumbnail_50x50(self,obj):
        return obj.image_50x50_url()

    def get_thumbnail_300x400(self,obj):
        return obj.image_300x400_url()

    def get_thumbnail_400x400(self,obj):
        return obj.image_400x400_url()

    def get_is_portrait(self,obj):
        return obj.image_is_portrait()


class SouscriptionSerializer(serializers.ModelSerializer):
    souscription_id = serializers.IntegerField(source='id')
    livre = LivreApiSerializer()

    class Meta:
        model = Souscription
        fields = ('souscription_id', 'livre','quantite','merged','prix','rang','souscription_pourcent')

class DiscountSerializer(serializers.ModelSerializer):
    discount_id = serializers.IntegerField(source='id')
    code = serializers.SerializerMethodField('get_dicount_code')
    description = serializers.SerializerMethodField()
    reduction = serializers.SerializerMethodField()

    class Meta:
        model = Discount
        fields = ('discount_id','code','description','reduction')

    def get_dicount_code(self, obj):
        return obj.discount.code

    def get_description(self, obj):
        return str(obj.discount)

    def get_reduction(self, obj):
        return obj.get_reduction()

class NotificationApiSerializer(serializers.ModelSerializer):
    api_message_type = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('api_message_type','image_url','texte','timestamp','reload','link_url')

    def get_api_message_type(self, obj):
        return "NOTIF"

    def get_timestamp(self,obj):
        return str(timezone.now())

class PanierApiSerializer(serializers.ModelSerializer):
    api_message_type = serializers.SerializerMethodField()
    souscription_set = SouscriptionSerializer(many=True)
    discount_set = DiscountSerializer(many=True)
    shipping = serializers.SerializerMethodField('get_frais_envoi')
    shipping_country = serializers.SerializerMethodField('get_pays_envoi')
    info_facturation = serializers.SerializerMethodField()
    info_livraison = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    nbArticles = serializers.SerializerMethodField()
    total_sans_discount_ni_taxes = serializers.SerializerMethodField()

    class Meta:
        model = Commande
        fields = ('api_message_type','souscription_set','discount_set','shipping','shipping_country','nbArticles',\
                  'livraison_autre_adresse','info_facturation','info_livraison','timestamp','prix','total_sans_discount_ni_taxes')

    def get_total_sans_discount_ni_taxes(self,obj):
        return obj.total_sans_discount_ni_taxes

    def get_api_message_type(self, obj):
        return "PANIER"

    def get_nbArticles(self,obj):
        return obj.nbArticles()

    def get_info_facturation(self, obj):
        if obj.adresse_fact:
            return AdresseSerializer(obj.adresse_fact,context=self.context).data
        else:
            return None

    def get_info_livraison(self, obj):
        if obj.adresse_livr:
            return AdresseSerializer(obj.adresse_livr,context=self.context).data
        else:
            return None

    def get_frais_envoi(self, obj):
        return obj.get_frais_envoi()

    def get_pays_envoi(self,obj):
        return dict(countries)[obj.pays_livraison]

    def get_timestamp(self,obj):
        return str(timezone.now())

class StaffUserSerializer(serializers.ModelSerializer):
    thumbnail_50x50 = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    adresse = AdresseSerializer()

    class Meta:
        model = BiblioUser
        fields = ('thumbnail_50x50','url','email','adresse')

    def get_thumbnail_50x50(self,obj):
        return obj.avatar_50x50_url()

    def get_url(self,obj):
        return obj.profil_url()


class StaffSouscriptionSerializer(serializers.ModelSerializer):
    souscription_id = serializers.IntegerField(source='id')
    livre = serializers.SerializerMethodField()
    # ajout 1 serializer
    thumbnail_50x50 = serializers.SerializerMethodField()
    prix_unitaire = serializers.SerializerMethodField()

    class Meta:
        model = Souscription
        fields = ('souscription_id', 'etat','quantite','prix','livre','thumbnail_50x50', 'prix_unitaire')

    def get_prix_unitaire(self, obj):
        return obj.prix / obj.quantite

    def get_livre(self,obj):
        return obj.livre.titre

    # ajout 1def
    def get_thumbnail_50x50(self,obj):
        return obj.livre.image_50x50_url()


class CommandeSerializer(serializers.ModelSerializer):
    souscription_set = StaffSouscriptionSerializer(many=True)
    nbArticles = serializers.SerializerMethodField()
    client = StaffUserSerializer()
    shipping = serializers.SerializerMethodField('get_frais_envoi')
    adresse_fact = AdresseSerializer()
    adresse_livr = AdresseSerializer()

    class Meta:
        model = Commande
        fields = ('etat','client','souscription_set', 'nbArticles', 'prix','no_commande','date','shipping','adresse_fact','adresse_livr')

    def get_nbArticles(self,obj):
        return obj.nbArticles()

    def get_frais_envoi(self, obj):
        return obj.get_frais_envoi()


class TextPropositionSerializer(serializers.ModelSerializer):
    auteur = BiblioUserSerializer()
    nb_votes = serializers.SerializerMethodField()
    livre = LivreMiniSerializer()
    class Meta:
        model=TextProposition
        fields = ('id','type','valeur','auteur','nb_votes','chosen','livre')

    def get_nb_votes(self,obj):
        return obj.vote_set.count()

class CharPropositionSerializer(serializers.ModelSerializer):
    auteur = BiblioUserSerializer()
    nb_votes = serializers.SerializerMethodField()
    livre = LivreMiniSerializer()
    type = serializers.SerializerMethodField()
    class Meta:
        model=CharProposition
        fields = ('id','valeur','auteur','nb_votes','livre','type')

    def get_nb_votes(self,obj):
        return obj.vote_set.count()

    def get_type(self,obj):
        return obj.get_type()

class NumberPropositionSerializer(serializers.ModelSerializer):
    auteur = BiblioUserSerializer()
    nb_votes = serializers.SerializerMethodField()
    livre = LivreMiniSerializer()
    type = serializers.SerializerMethodField()

    class Meta:
        model=NumberProposition
        fields = ('id','valeur','auteur','nb_votes','livre','type')

    def get_nb_votes(self,obj):
        return obj.vote_set.count()

    def get_type(self,obj):
        return obj.get_type()

class ImagePropositionSerializer(serializers.ModelSerializer):
    thumbnail_260x260 = serializers.SerializerMethodField()
    auteur = BiblioUserSerializer()
    nb_votes = serializers.SerializerMethodField()
    livre = LivreMiniSerializer()
    type = serializers.SerializerMethodField()

    class Meta:
        model=ImageProposition
        fields = ('id','valeur','thumbnail_260x260','nb_votes','auteur','chosen','livre','type')

    def get_nb_votes(self,obj):
        return obj.vote_set.count()

    def get_thumbnail_260x260(self,obj):
        return obj.image_260x260()

    def get_type(self,obj):
        return obj.get_type()

class SondageApiSerializer(serializers.ModelSerializer):
    titres = serializers.SerializerMethodField()
    prix = serializers.SerializerMethodField()
    couvertures = serializers.SerializerMethodField()
    extraits = serializers.SerializerMethodField()
    extraits_img = serializers.SerializerMethodField()
    biographies = serializers.SerializerMethodField()
    nbvotes = serializers.SerializerMethodField()
    nb_extraits_choisis = serializers.SerializerMethodField()

    class Meta:
        model=Livre
        fields = ('titres','prix','couvertures','extraits','extraits_img','biographies','instructions','nbvotes','nb_extraits_choisis')

    def get_titres(self,obj):
        if self.context.has_key('presouscription_transform') and self.context['presouscription_transform']:
            qset=CharProposition.objects.filter(livre=obj,deleted=False)
        else:
            qset=CharProposition.objects.filter(livre=obj,private=False)
        return CharPropositionSerializer(qset, many=True,context=self.context).data

    def get_prix(self,obj):
        if self.context.has_key('presouscription_transform') and self.context['presouscription_transform']:
            qset=NumberProposition.objects.filter(livre=obj,deleted=False)
        else:
            qset=NumberProposition.objects.filter(livre=obj,private=False)
        return NumberPropositionSerializer(qset, many=True,context=self.context).data

    def get_couvertures(self,obj):
        if self.context.has_key('presouscription_transform') and self.context['presouscription_transform']:
            qset=ImageProposition.objects.filter(livre=obj,type='COVER',deleted=False)
        else:
            qset=ImageProposition.objects.filter(livre=obj,type='COVER',private=False)
        return ImagePropositionSerializer(qset, many=True,context=self.context).data

    def get_extraits(self,obj):
        qset=TextProposition.objects.filter(livre=obj,type='EXTRA').order_by('-chosen')
        return TextPropositionSerializer(qset, many=True,context=self.context).data

    def get_extraits_img(self,obj):
        qset=ImageProposition.objects.filter(livre=obj,type='EXTRA').order_by('-chosen')
        return ImagePropositionSerializer(qset, many=True,context=self.context).data

    def get_nb_extraits_choisis(self,obj):
        return TextProposition.objects.filter(livre=obj,type='EXTRA',chosen=True).count() + \
               ImageProposition.objects.filter(livre=obj,type='EXTRA',chosen=True).count()

    def get_biographies(self,obj):
        if self.context.has_key('presouscription_transform') and self.context['presouscription_transform']:
            qset=TextProposition.objects.filter(livre=obj,type='BIO',deleted=False)
        else:
            qset=TextProposition.objects.filter(livre=obj,type='BIO',private=False)
        return TextPropositionSerializer(qset, many=True,context=self.context).data

    def get_nbvotes(self,obj):
        count=Vote.objects.filter(proposition__livre=obj).count()
        return count

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model=Tag
        fields = ('text',)

class SelectSerializer(serializers.Serializer):
    display = serializers.CharField()
    value = serializers.CharField()

class PropositionRelatedField(serializers.RelatedField):
    """
    A custom field to use for the `proposition`
    """

    def to_representation(self, value):
        """
        Serialize tagged objects to a simple textual representation.
        """
        typed_value = value.getTypedProposition()
        if isinstance(typed_value, TextProposition):
            serializer = TextPropositionSerializer(typed_value)
        elif isinstance(typed_value, NumberProposition):
            serializer = NumberPropositionSerializer(typed_value)
        elif isinstance(typed_value, CharProposition):
            serializer = CharPropositionSerializer(typed_value)
        elif isinstance(typed_value, ImageProposition):
            serializer = ImagePropositionSerializer(typed_value)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data


class VoteSerializer(serializers.ModelSerializer):
    user = BiblioUserSerializer()
    proposition = PropositionRelatedField(read_only=True)
    class Meta:
        model=Vote
        fields = ('user', 'proposition')

class FollowSerializer(serializers.ModelSerializer):
    qui = BiblioUserSerializer()
    suit = BiblioUserSerializer()
    class Meta:
        model=Follow
        fields = ('qui', 'suit','lien')

class TimelineObjectRelatedField(serializers.RelatedField):
    """
    A custom field to use for the `tagged_object` generic relationship.
    """

    def to_representation(self, value):
        """
        Serialize tagged objects to a simple textual representation.
        """
        if isinstance(value, Commande):
            serializer = PanierApiSerializer(value)
        elif isinstance(value, TextProposition):
            serializer = TextPropositionSerializer(value)
        elif isinstance(value, NumberProposition):
            serializer = NumberPropositionSerializer(value)
        elif isinstance(value, CharProposition):
            serializer = CharPropositionSerializer(value)
        elif isinstance(value, ImageProposition):
            serializer = ImagePropositionSerializer(value)
        elif isinstance(value, Commentaire):
            serializer = CommentaireSerializer(value)
        elif isinstance(value, Vote):
            serializer = VoteSerializer(value)
        elif isinstance(value, Souscription):
            serializer = SouscriptionSerializer(value)
        elif isinstance(value, Follow):
            serializer = FollowSerializer(value)
        elif isinstance(value, Livre):
            serializer = SouscriptionApiSerializer(value)
        elif isinstance(value, BiblioUser):
            serializer = BiblioUserSerializer(value)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data


class TimelineCommentaireSerializer(serializers.ModelSerializer):
    user = BiblioUserSerializer()
    class Meta:
        model = TimelineCommentaire
        fields = ('id','user','contenu','date','timeline')


class TimelineApiSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()
    partage = MiniUserSerializer(many=True)
    api_message_type = serializers.SerializerMethodField()
    content_object = TimelineObjectRelatedField(read_only=`True`)
    timelinecommentaire_set = TimelineCommentaireSerializer(many=True)
    class Meta:
        model=Timeline
        fields = ('id','api_message_type','user','timestamp','action','content_object','timelinecommentaire_set','partage','private')

    def get_api_message_type(self, obj):
        return "TIMELINE"
