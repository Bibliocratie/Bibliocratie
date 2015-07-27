# -*- coding: utf-8 -*-
import os
from django import forms
from djangular.forms import NgModelFormMixin, NgFormValidationMixin
from djangular.forms.widgets import CheckboxChoiceInput
from django.utils.translation import gettext as _
from django_countries.widgets import CountrySelectWidget
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.views import password_reset
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model


from bibliocratie.models import *
from bibliocratie.mixin import Bootstrap3Form, Bootstrap3ModelForm
from bibliocratie.widgets import CheckboxIWidget


ERROR_MESSAGE = _("L'identifiant et le mot de passe ne correspondent pas.")
ERROR_MESSAGE_RESTRICTED = _("Vous n'avez pas l'autorisation necessaire")
ERROR_MESSAGE_INACTIVE = _("Ce compte est inactif.")
ERROR_MESSAGE_EMAIL_ALREADY_USED = _("Ce compte existe deja. Veuillez modifier vos informations.")
ERROR_MESSAGE_PSEUDO_ALREADY_USED = _("Cet identifiant existe deja. Veuillez modifier vos informations.")


class BibliocratieAuthenticationForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3Form):
    form_name = 'login_form'
    scope_prefix = 'login_data'
    email = forms.EmailField(label=_("Mail"), max_length=75)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, min_length=3)
    message_incorrect_password = ERROR_MESSAGE
    message_inactive = ERROR_MESSAGE_INACTIVE

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if (self.user_cache is None):
                raise forms.ValidationError(self.message_incorrect_password)
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.message_inactive)
        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class BibliocratieSignupForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'signup_form'
    scope_prefix = 'signup_data'
    email = forms.EmailField(label=_("Mail"), max_length=75)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, min_length=3)
    password_verif = forms.CharField(label=_("Confirmation mot de passe"), widget=forms.PasswordInput, min_length=3)
    pseudo = forms.CharField(label=_("Nom utilisateur"), min_length=3,error_messages={'invalide': _('Le pseudo doit faire au moins 3 caracteres')})
    message_incorrect_password = ERROR_MESSAGE
    message_inactive = ERROR_MESSAGE_INACTIVE
    message_existing_email = ERROR_MESSAGE_EMAIL_ALREADY_USED
    message_existing_pseudo = ERROR_MESSAGE_PSEUDO_ALREADY_USED

    class Meta:
        model = BiblioUser
        fields = ('password','password_verif','pseudo','biographie','lieu')

    def __init__(self, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        super(BibliocratieSignupForm, self).__init__(*args, **kwargs)
        self.fields['password_verif'].widget.attrs['match'] = 'signup_data.password'


    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        password_verif = self.cleaned_data.get('password_verif')
        pseudo = self.cleaned_data.get('pseudo')

        if email and password and password_verif:
            if password != password_verif:
                raise forms.ValidationError(self.message_incorrect_password)
            if BiblioUser.objects.filter(username=pseudo).count()!=0:
                raise forms.ValidationError(self.message_existing_pseudo)
            try:
                user = get_user_model().objects.create_user(email=email, password=password, username=pseudo)
            except IntegrityError as ie:
                raise forms.ValidationError(self.message_existing_email)

            self.user_cache = authenticate(email=email, password=password)

            if (self.user_cache is None):
                raise forms.ValidationError(self.message_existing_email)
                # raise forms.ValidationError(self.message_incorrect_password)
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.message_inactive)
        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


# class UserBioLieuForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
#     form_name = 'biolieu_form'
#     scope_prefix = 'biolieu_data'
#
#     class Meta:
#         model = BiblioUser
#         fields = ('biographie','lieu')
#
# class UserPrefForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
#     form_name = 'userpref_form'
#     scope_prefix = 'userpref_data'
#
#     class Meta:
#         model = BiblioUser
#         fields = ('biographie','lieu')



class BibliocratieRecoverForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3Form):
    form_name = 'recover_form'
    scope_prefix = 'recover_data'
    email = forms.EmailField(label=_("Mail"), max_length=75)

    def clean(self):
        UserModel = get_user_model()
        email = self.cleaned_data["email"]
        active_users = UserModel._default_manager.filter(
            email__iexact=email, is_active=True)
        if active_users.count() != 1:
            raise forms.ValidationError(_("Cet utilisateur est inconnu"))
        for user in active_users:
            # Make sure that no email is sent to a user that actually has
            # a password marked as unusable
            if not user.has_usable_password():
                continue
            current_site = get_current_site(self)
            site_name = current_site.name
            domain = current_site.domain

            subject = _("Reinitialiser votre mot de passe")
            to = [user.email]
            ctx={
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'user': user,
                    'email': user.email,
                    'domain': domain,
                    'site_name': site_name,
                    'protocol': 'http',
                    'token': default_token_generator.make_token(user),
            }

            message = get_template('mails/password_reset.html').render(Context(ctx))
            msg = EmailMessage(subject, message, to=to)
            msg.content_subtype = 'html'
            msg.send()
        return self.cleaned_data


class BibliocratieCouponForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3Form):
    form_name = 'coupon_form'
    scope_prefix = 'coupon_data'
    coupon_code = forms.CharField(label=_('Code reduction'))
    message_incorrect_coupon = _("Votre code reduction n'est pas valide ")

    def clean(self):
        code = self.cleaned_data.get('coupon_code')
        try:
            self.discount = DiscountCode.objects.get(code=code)
        except DiscountCode.DoesNotExist:
            raise forms.ValidationError(self.message_incorrect_coupon)

        return self.cleaned_data


class AdresseForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'adresse_form'
    scope_prefix = 'adresse_data'
    prenom = forms.CharField(label=_('Prenom'), min_length=3)
    nom = forms.RegexField(r'^[A-Z][a-z -]?', label='Nom',
                           error_messages={'invalid': _('Les noms de famille doivent démarrer par une majuscule')})
    adresse = forms.CharField(label='Adresse', min_length=3)
    complement_adresse = forms.CharField(label=_('Complement d\'adresse'), required=False)
    code_postal = forms.CharField(label=_('Code postal'), min_length=3, max_length=20)
    ville = forms.CharField(label='Ville', min_length=3, max_length=20)
    phone = forms.RegexField(r'^\+?[0-9 .-]{4,25}$', label='Telephone',
                             error_messages={
                                 'invalid': _('Le numero de telephone doit faire entre 4-25 caracteres et commencer par +')})
    pays = CountryField(blank=False,error_messages={'invalid': _('Pas de pays renseigne')})

    class Meta:
        model = Adresse
        fields = ('prenom', 'nom', 'adresse', 'complement_adresse', 'code_postal', 'ville', 'pays', 'phone','entreprise')
        widgets = {
            'pays': CountrySelectWidget(layout=u'{widget}<img class="country-select-flag" id="{flag_id}" style="width:16px; margin-top: -24px;margin-left: 7px; position: absolute; src="{country.flag}">'),
        }

    def clean_pays(self):
        pays = self.cleaned_data['pays']
        if pays=="":
            raise forms.ValidationError(
                _("Le pays doit etre renseigne"),
                code='invalid',
                params={},
            )

        return pays

    def setFormName(self, form_name):
        self.form_name = form_name

    def setScopePrefix(self, scope_prefix):
        self.scope_prefix = scope_prefix


class CheckoutForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3Form):
    form_name = 'checkout_form'
    scope_prefix = 'checkout_data'

    diff_address = forms.BooleanField(label=_('Livrer a une adresse différente?'),
                                      required=False, initial=False)


class ImagePropositionForm(NgModelFormMixin, Bootstrap3ModelForm):
    form_name = 'image_form'
    scope_prefix = 'image_data'
    class Meta:
        model = ImageProposition
        fields = ('valeur',)


class NumberPropositionForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'number_form'
    scope_prefix = 'number_data'
    class Meta:
        model = NumberProposition
        fields = ('valeur',)


class CharPropositionForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'char_form'
    scope_prefix = 'char_data'
    class Meta:
        model = CharProposition
        fields = ('valeur',)

class TextPropositionForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'text_form'
    scope_prefix = 'text_data'
    class Meta:
        model = TextProposition
        fields = ('valeur',)

class CommentaireForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'comment_form'
    scope_prefix = 'comment_data'
    class Meta:
        model = Commentaire
        fields = ('contenu',)

class LancementForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'lancement_form'
    scope_prefix = 'lancement_data'
    class Meta:
        model = Livre
        fields = ('titre',)

    def clean_titre(self):
        titre = self.cleaned_data['titre']
        search = Livre.objects.filter(slug=slugify(titre), is_active=True).count()
        if search>0:
            raise forms.ValidationError(
                _("Le titre existe déjà. Si vous voulez éditer un projet existant veuillez consulter votre profil"),
                code='invalid',
                params={},
            )
        return titre


class LancementDebutForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'lancement_debut_form'
    scope_prefix = 'lancement_debut_data'

    class Meta:
        model = Livre
        fields = ('pre_souscription','maquette', 'couverture','type_encre','genre','category')
        widgets = {
            'maquette': CheckboxIWidget(label="Bibliocratie réalise la maquette de mon livre"),
            'couverture' : CheckboxIWidget(label="Bibliocratie réalise la couverture de mon livre"),
        }

class LancementFichiersForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'lancement_fichier_form'
    scope_prefix = 'lancement_fichier_data'

    class Meta:
        model = Livre
        fields = ('fichier_auteur','maquete_couverture','image_couverture')


class LancementInterneForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'lancement_interne_form'
    scope_prefix = 'lancement_interne_data'
    # nb_carac = forms.IntegerField(min_value=3291, error_messages={'min_value': "Le nombre minimumde caracteres est 3291"})

    class Meta:
        model = Livre
        fields = ('format','nb_carac','nb_pages','nb_pages_couleur','nb_pages_nb','largeur_mm','hauteur_mm','nb_chapitres')

    def clean_format(self):
        format = self.cleaned_data['format']
        if format=='':
            raise forms.ValidationError(
                _("Veuillez choisir un format"),
                code='invalid',
                params={},
            )
        return format

    def clean(self):
        cleaned_data = super(LancementInterneForm, self).clean()
        error_message = "erreur : "
        for error in self.errors:
            if error in ['format']:
                for msg in self.errors[error]:
                    error_message += msg + " / "
        if self.errors:
            raise forms.ValidationError(error_message)


class LancementCouvertureForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'lancement_couverture_form'
    scope_prefix = 'lancement_couverture_data'

    class Meta:
        model = Livre
        fields = ('modele_couverture','instructions_maquette')

class LancementPrixDateForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'lancement_prixdate_form'
    scope_prefix = 'lancement_prixdate_data'
    nb_exemplaires_cible = forms.IntegerField(min_value=50, error_messages={'min_value': "Le nombre d'exemplaires minimum est 50"})
    class Meta:
        model = Livre
        fields = ('pre_souscription','nb_exemplaires_cible', 'cout_production', 'prix_vente','date_souscription','date_feedback','nb_jours_campagne')
        widgets = {
            'date_souscription' : forms.widgets.DateTimeInput(format=('%Y-%m-%d')),
            'date_feedback' : forms.widgets.DateTimeInput(format=('%Y-%m-%d')),
        }


    def clean_date_souscription(self):
        date_souscription = self.cleaned_data['date_souscription']
        #date souscription doit etre un mercredi dans le futur
        if not date_souscription:
            return

        if date_souscription.weekday()!=2:
            raise forms.ValidationError(
                _("La date de souscription n'est pas un mercredi"),
                code='invalid',
                params={},
            )
        if date_souscription < timezone.now():
            raise forms.ValidationError(
                _("La date de souscription doit etre dans le futur"),
                code='invalid',
                params={},
            )
        return date_souscription

    def clean_date_feedback(self):
        date_feedback = self.cleaned_data['date_feedback']
        #date feedback doit etre un mercredi dans le futur
        if not date_feedback:
            return

        if date_feedback.weekday()!=2:
            raise forms.ValidationError(
                _("La date de pre-souscription n'est pas un mercredi"),
                code='invalid',
                params={},
            )
        if date_feedback < timezone.now():
            raise forms.ValidationError(
                _("La date de pre-souscription doit etre dans le futur"),
                code='invalid',
                params={},
            )
        return date_feedback

    def clean_nb_jours_campagne(self):
        nb_jours_campagne = self.cleaned_data['nb_jours_campagne']
        #date feedback doit etre un mercredi dans le futur

        if not nb_jours_campagne:
            raise forms.ValidationError(
                _("Veuillez choisir la duree de votre souscription"),
                code='invalid',
                params={},
            )

        if nb_jours_campagne<10:
            raise forms.ValidationError(
                _("La campagne doit durer au moins 10 jours"),
                code='invalid',
                params={},
            )

        return nb_jours_campagne


    def clean_prix_vente(self):
        try:
            prix_vente = self.cleaned_data['prix_vente']
        except:
            raise forms.ValidationError(
                _("Le prix de vente n'est pas indique"),
                code='invalid',
                params={},
            )
        try:
            cout_production = self.cleaned_data['cout_production']
        except:
            return

        if prix_vente < cout_production :
            raise forms.ValidationError(
                _('Le prix de vente ne peut etre inferieur au cout de production: %(value)s'),
                code='invalid',
                params={'value': cout_production},
            )
        return prix_vente

    def clean(self):
        cleaned_data = super(LancementPrixDateForm, self).clean()
        error_message = "erreur : "
        for error in self.errors:
            if error in ['date_souscription','prix_vente','date_feedback','date_souscription']:
                for msg in self.errors[error]:
                    error_message += msg + " / "
        if self.errors:
            raise forms.ValidationError(error_message)


class LancementFinForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'lancement_fin_form'
    scope_prefix = 'lancement_fin_data'
    class Meta:
        model = Livre
        fields = ('certif_modification', 'certif_proprio','certif_promo','certif_exclu','certif_mineur','certif_coauteur','remarques')
        widgets = {
            'certif_modification': CheckboxIWidget(label=_("Je certifie avoir compris et accepter qu'aucune modification de l'ouvrage telecharge (sur le fond comme sur la forme, sauf pour l'orthographe) n'est possible, apres validation definitive du projet par l'equipe de Bibliocratie.")),
            'certif_proprio' : CheckboxIWidget(label=_("Je certifie etre le proprietaire des droits de la totalite des textes, images, videos, polices et, generalement, de tout ce qui constitue mon livre et sa presentation, sur le fond comme sur la forme. J'ai compris que toute oeuvre en infraction avec le droit d'auteur sera supprimee du site sans aucun preavis, ni aucun droit a compensation.")),
            'certif_promo': CheckboxIWidget(label=_("J'autorise expressement le site Bibliocratie a utiliser gratuitement l'ensemble des contenus de mon livre en vue de sa promotion, ainsi que, dans la limite de sa duree de souscription, en vue de sa vente, de sa fabrication et de sa livraison.")),
            'certif_exclu' : CheckboxIWidget(label=_("Je certifie que mon livre n'est pas propose a la vente comme cede gratuitement aupres d'un distributeur physique ou numerique, que ce soit sous la forme d'une souscription, d'une diffusion imprimee ou numerique. Je m'engage a respecter cette clause d'exclusivite avec Bibliocratie a partir de l'envoi de ce formulaire et jusqu'a la fin de mon eventuelle souscription."),),
            'certif_mineur' : CheckboxIWidget(label=_("Je suis mineur. Je m'engage a fournir une autorisation parentale a Bibliocratie."),),
            'certif_coauteur' : CheckboxIWidget(label=_("J'ai cree cet ouvrage avec d'autre auteurs. Je m'engage a fournir l'autorisation de mes co-auteurs a Bibliocratie."),),
        }

class LivreForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'livre_form'
    scope_prefix = 'livre_data'

    class Meta:
        model = Livre
        fields = ('id','resume','biographie','instructions','pourquoi_ce_livre',
                  'extrait1_txt','extrait1_type','extrait1_img',
                  'extrait2_txt','extrait2_type','extrait2_img',
                  'extrait3_txt','extrait3_type','extrait3_img',
                  'extrait4_txt','extrait4_type','extrait4_img',
                  'tags','titre','prix_vente','cout_production',
                  "type_titres","type_prix","type_couvertures","type_extraits","type_biographies",
                  "instructions","instructions_titre","instructions_prix","instructions_couverture",
                  "instructions_extraits","instructions_biographie","phrase_cle","annonces"
        )


class LivreFileForm(forms.ModelForm):
    class Meta:
        model = Livre
        fields = ('extrait1_img','extrait2_img','extrait3_img','extrait4_img','image_couverture')

class BiblioUserFileForm(forms.ModelForm):
    class Meta:
        model = BiblioUser
        fields = ('avatar',)

class BiblioUserForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'biblio_user_form'
    scope_prefix = 'biblio_user_data'

    class Meta:
        model = BiblioUser
        fields = ('username','site_internet','lieu','biographie','avatar',
                  'pref_actu','pref_adol','pref_art','pref_bd','pref_beau','pref_cuisine','pref_dict','pref_droit',
                  'pref_entreprise','pref_erotisme','pref_esoterisme','pref_etude','pref_famille','pref_fantaisie',
                  'pref_histoire','pref_humour','pref_informatique','pref_litterature','pref_sentiment','pref_enfant',
                  'pref_loisirs','pref_manga','pref_nature','pref_policier','pref_religion','pref_sciencefi','pref_sciencehu',
                  'pref_sciencete','pref_scolaire','pref_sport','pref_tourisme','pref_photo',
        )
        widgets = {
            # 'lieu': forms.TextInput(attrs={'googleplace': 'googleplace'}),
            'pref_actu': CheckboxIWidget(),
            'pref_adol': CheckboxIWidget(),
            'pref_art': CheckboxIWidget(),
            'pref_bd': CheckboxIWidget(),
            'pref_beau': CheckboxIWidget(),
            'pref_cuisine': CheckboxIWidget(),
            'pref_dict': CheckboxIWidget(),
            'pref_droit': CheckboxIWidget(),
            'pref_entreprise': CheckboxIWidget(),
            'pref_erotisme': CheckboxIWidget(),
            'pref_esoterisme': CheckboxIWidget(),
            'pref_etude': CheckboxIWidget(),
            'pref_famille': CheckboxIWidget(),
            'pref_fantaisie': CheckboxIWidget(),
            'pref_histoire': CheckboxIWidget(),
            'pref_humour': CheckboxIWidget(),
            'pref_informatique': CheckboxIWidget(),
            'pref_litterature': CheckboxIWidget(),
            'pref_sentiment': CheckboxIWidget(),
            'pref_enfant': CheckboxIWidget(),
            'pref_loisirs': CheckboxIWidget(),
            'pref_manga': CheckboxIWidget(),
            'pref_nature': CheckboxIWidget(),
            'pref_policier': CheckboxIWidget(),
            'pref_religion': CheckboxIWidget(),
            'pref_sciencefi': CheckboxIWidget(),
            'pref_sciencehu': CheckboxIWidget(),
            'pref_sciencete': CheckboxIWidget(),
            'pref_scolaire': CheckboxIWidget(),
            'pref_sport': CheckboxIWidget(),
            'pref_tourisme': CheckboxIWidget(),
            'pref_photo': CheckboxIWidget(),
        }


class BiblioUserEmailForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'biblio_user_form'
    scope_prefix = 'biblio_user_data'

    class Meta:
        model = BiblioUser
        fields = ('email','username','site_internet','lieu','biographie','avatar',
                  'pref_actu','pref_adol','pref_art','pref_bd','pref_beau','pref_cuisine','pref_dict','pref_droit',
                  'pref_entreprise','pref_erotisme','pref_esoterisme','pref_etude','pref_famille','pref_fantaisie',
                  'pref_histoire','pref_humour','pref_informatique','pref_litterature','pref_sentiment','pref_enfant',
                  'pref_loisirs','pref_manga','pref_nature','pref_policier','pref_religion','pref_sciencefi','pref_sciencehu',
                  'pref_sciencete','pref_scolaire','pref_sport','pref_tourisme','pref_photo',
        )
        widgets = {
            'pref_actu': CheckboxIWidget(),
            'pref_adol': CheckboxIWidget(),
            'pref_art': CheckboxIWidget(),
            'pref_bd': CheckboxIWidget(),
            'pref_beau': CheckboxIWidget(),
            'pref_cuisine': CheckboxIWidget(),
            'pref_dict': CheckboxIWidget(),
            'pref_droit': CheckboxIWidget(),
            'pref_entreprise': CheckboxIWidget(),
            'pref_erotisme': CheckboxIWidget(),
            'pref_esoterisme': CheckboxIWidget(),
            'pref_etude': CheckboxIWidget(),
            'pref_famille': CheckboxIWidget(),
            'pref_fantaisie': CheckboxIWidget(),
            'pref_histoire': CheckboxIWidget(),
            'pref_humour': CheckboxIWidget(),
            'pref_informatique': CheckboxIWidget(),
            'pref_litterature': CheckboxIWidget(),
            'pref_sentiment': CheckboxIWidget(),
            'pref_enfant': CheckboxIWidget(),
            'pref_loisirs': CheckboxIWidget(),
            'pref_manga': CheckboxIWidget(),
            'pref_nature': CheckboxIWidget(),
            'pref_policier': CheckboxIWidget(),
            'pref_religion': CheckboxIWidget(),
            'pref_sciencefi': CheckboxIWidget(),
            'pref_sciencehu': CheckboxIWidget(),
            'pref_sciencete': CheckboxIWidget(),
            'pref_scolaire': CheckboxIWidget(),
            'pref_sport': CheckboxIWidget(),
            'pref_tourisme': CheckboxIWidget(),
            'pref_photo': CheckboxIWidget(),
        }


class BiblioUserPrefForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'biblio_user_form'
    scope_prefix = 'biblio_user_data'

    class Meta:
        model = BiblioUser
        fields = ('lieu','biographie','need_more_info',
                  'pref_actu','pref_adol','pref_art','pref_bd','pref_beau','pref_cuisine','pref_dict','pref_droit',
                  'pref_entreprise','pref_erotisme','pref_esoterisme','pref_etude','pref_famille','pref_fantaisie',
                  'pref_histoire','pref_humour','pref_informatique','pref_litterature','pref_sentiment','pref_enfant',
                  'pref_loisirs','pref_manga','pref_nature','pref_policier','pref_religion','pref_sciencefi','pref_sciencehu',
                  'pref_sciencete','pref_scolaire','pref_sport','pref_tourisme','pref_photo',
        )
        widgets = {
            'pref_actu': CheckboxIWidget(),
            'pref_adol': CheckboxIWidget(),
            'pref_art': CheckboxIWidget(),
            'pref_bd': CheckboxIWidget(),
            'pref_beau': CheckboxIWidget(),
            'pref_cuisine': CheckboxIWidget(),
            'pref_dict': CheckboxIWidget(),
            'pref_droit': CheckboxIWidget(),
            'pref_entreprise': CheckboxIWidget(),
            'pref_erotisme': CheckboxIWidget(),
            'pref_esoterisme': CheckboxIWidget(),
            'pref_etude': CheckboxIWidget(),
            'pref_famille': CheckboxIWidget(),
            'pref_fantaisie': CheckboxIWidget(),
            'pref_histoire': CheckboxIWidget(),
            'pref_humour': CheckboxIWidget(),
            'pref_informatique': CheckboxIWidget(),
            'pref_litterature': CheckboxIWidget(),
            'pref_sentiment': CheckboxIWidget(),
            'pref_enfant': CheckboxIWidget(),
            'pref_loisirs': CheckboxIWidget(),
            'pref_manga': CheckboxIWidget(),
            'pref_nature': CheckboxIWidget(),
            'pref_policier': CheckboxIWidget(),
            'pref_religion': CheckboxIWidget(),
            'pref_sciencefi': CheckboxIWidget(),
            'pref_sciencehu': CheckboxIWidget(),
            'pref_sciencete': CheckboxIWidget(),
            'pref_scolaire': CheckboxIWidget(),
            'pref_sport': CheckboxIWidget(),
            'pref_tourisme': CheckboxIWidget(),
            'pref_photo': CheckboxIWidget(),
        }

class BiblioUserBiolieu(NgModelFormMixin, NgFormValidationMixin, Bootstrap3ModelForm):
    form_name = 'biblio_userbiolieu_form'
    scope_prefix = 'biblio_userbiolieu_data'

    class Meta:
        model = BiblioUser
        fields = ('lieu','biographie','avatar')


class PreferenceForm(NgModelFormMixin,forms.ModelForm):
    form_name = 'preference_form'
    scope_prefix = 'preference_data'
    class Meta:
        model = UserPreference
        fields = ('FollowingNewCommandeNotifyMe','FollowingNewPropositionNotifyMe','FollowingNewCommentaireNotifyMe',
                  'FollowingNewVoteNotifyMe','FollowingNewFollowNotifyMe','FollowingOnlineNotifyMe')

class ContactForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3Form):
    form_name = 'contact_form'
    scope_prefix = 'contact_data'
    prenom = forms.CharField(label='Prenom', min_length=3, max_length=80,required=True,)
    nom = forms.CharField(label='Nom', min_length=3, max_length=80,required=True,)
    mail = forms.EmailField(label='Email', min_length=3, max_length=80,required=True,)
    telephone = forms.RegexField(r'^\+?[0-9 .-]{4,25}$', label='Telephone',
                                 error_messages={'invalid': _('Les numéros de téléphone ont de 4 a 25 chiffres et peuvent commencer par +')})
    message = forms.CharField(label='Votre message', required=True, widget=forms.Textarea(attrs={'cols': '80', 'rows': '3'}))


# class ChequeForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3Form):
#     form_name = 'cheque_form'
#     scope_prefix = 'cheque_data'
#
#     email = forms.EmailField(label='Email')
#     titre = forms.CharField(label="titre du livre")
#     quantite = forms.IntegerField(label=_('Quantite'))
#     #Facturation
#     fact_prenom = forms.CharField(label=_('Prenom facturation'), min_length=3)
#     fact_nom = forms.RegexField(r'^[A-Z][a-z -]?', label=_('Nom facturation'),
#                            error_messages={'invalide': _('Les noms de famille doivent démarrer par une majuscule')})
#     fact_adresse = forms.CharField(label='Adresse facturation', min_length=3)
#     fact_entreprise = forms.CharField(label='Entreprise facturation', max_length=100)
#     fact_complement_adresse = forms.CharField(label=_('Complement d\'adresse facturation'), required=False)
#     fact_code_postal = forms.CharField(label=_('Code postal facturation'), min_length=3, max_length=20)
#     fact_ville = forms.CharField(label='Ville facturation', min_length=3, max_length=20)
#     fact_phone = forms.RegexField(r'^\+?[0-9 .-]{4,25}$', label='Telephone facturation',
#                              error_messages={
#                                  'invalid': _('Le numero de telephone doit faire entre 4-25 caracteres et commencer par +')})
#     fact_pays = CountryField(error_messages={'invalide': _('Pas de pays renseigne')})
#
#     #Livraison
#     livr_prenom = forms.CharField(label=_('Prenom livraison'), min_length=3)
#     livr_nom = forms.RegexField(r'^[A-Z][a-z -]?', label=_('Nom'),
#                            error_messages={'invalide': _('Les noms de famille doivent démarrer par une majuscule')})
#     livr_adresse = forms.CharField(label='Adresse  livraison', min_length=3)
#     livr_entreprise = forms.CharField(label='Entreprise livraison', max_length=100)
#     livr_complement_adresse = forms.CharField(label=_('Complement d\'adresse livraison'), required=False)
#     livr_code_postal = forms.CharField(label=_('Code postal livraison'), min_length=3, max_length=20)
#     livr_ville = forms.CharField(label='Ville livraison', min_length=3, max_length=20)
#     livr_phone = forms.RegexField(r'^\+?[0-9 .-]{4,25}$', label='Telephone livraison',
#                              error_messages={
#                                  'invalid': _('Le numero de telephone doit faire entre 4-25 caracteres et commencer par +')})
#     livr_pays = CountryField(error_messages={'invalide': _('Pas de pays renseigne')})


# class AngularForm(NgModelFormMixin, NgFormValidationMixin, Bootstrap3FormMixin, forms.Form):
#     CONTINENT_CHOICES = (('am', 'America'), ('eu', 'Europe'), ('as', 'Asia'), ('af', 'Africa'),
#                          ('au', 'Australia'), ('oc', 'Oceania'), ('an', 'Antartica'),)
#     TRAVELLING_BY = (('foot', 'Foot'), ('bike', 'Bike'), ('mc', 'Motorcycle'), ('car', 'Car'),
#                      ('public', 'Public Transportation'), ('train', 'Train'), ('air', 'Airplane'),)
#     NOTIFY_BY = (('email', 'EMail'), ('phone', 'Phone'), ('sms', 'SMS'), ('postal', 'Postcard'),)
#
#     scope_prefix = 'subscribe_data'
#     form_name = 'my_form'
#     first_name = forms.CharField(label='First name', min_length=3, max_length=20)
#     last_name = forms.RegexField(r'^[A-Z][a-z -]?', label='Last name',
#         error_messages={'invalid': 'Last names shall start in upper case'})
#     sex = forms.ChoiceField(choices=(('m', 'Male'), ('f', 'Female')),
#         widget=forms.RadioSelect, error_messages={'invalid_choice': 'Please select your sex'})
#     email = forms.EmailField(label='E-Mail', required=True,
#         help_text='Please enter a valid email address')
#     subscribe = forms.BooleanField(label='Subscribe Newsletter',
#         initial=False, required=False)
#     phone = forms.RegexField(r'^\+?[0-9 .-]{4,25}$', label='Phone number',
#         error_messages={'invalid': 'Phone number have 4-25 digits and may start with +'})
#     birth_date = forms.DateField(label='Date of birth',
#         widget=forms.DateInput(attrs={'validate-date': '^(\d{4})-(\d{1,2})-(\d{1,2})$'}),
#         help_text='Allowed date format: yyyy-mm-dd')
#     continent = forms.ChoiceField(choices=CONTINENT_CHOICES, label='Living on continent',
#         error_messages={'invalid_choice': 'Please select your continent'})
#     weight = forms.IntegerField(min_value=42, max_value=95, label='Weight in kg',
#         error_messages={'min_value': 'You are too lightweight'})
#     height = FloatField(min_value=1.48, max_value=1.95, step=0.05, label='Height in meters',
#         error_messages={'max_value': 'You are too tall'})
#     traveling = forms.MultipleChoiceField(choices=TRAVELLING_BY, label='Traveling by',
#         help_text='Choose one or more carriers', required=True)
#     notifyme = forms.MultipleChoiceField(choices=NOTIFY_BY, label='Notify by',
#         widget=forms.CheckboxSelectMultiple, required=True,
#         help_text='Must choose at least one type of notification')
#     annotation = forms.CharField(label='Annotation', required=True,
#         widget=forms.Textarea(attrs={'cols': '80', 'rows': '3'}))
#     agree = forms.BooleanField(label='Agree with our terms and conditions',
#         initial=False, required=True)
#     password = forms.CharField(label='Password', widget=forms.PasswordInput,
#         validators=[validate_password],
#         help_text='The password is "secret"')
#     confirmation_key = forms.CharField(max_length=40, required=True, widget=forms.HiddenInput(),
#         initial='hidden value')
#
#     def clean(self):
#         if self.cleaned_data.get('first_name') == 'John' and self.cleaned_data.get('last_name') == 'Doe':
#             raise ValidationError('The full name "John Doe" is rejected by the server.')
#         return super(AngularForm, self).clean()
#
