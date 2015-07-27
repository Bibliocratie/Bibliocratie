from sorl.thumbnail.admin import AdminImageMixin
from django.contrib import admin
from django.conf import settings
from nested_inline.admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from django.utils.translation import ugettext_lazy as _
from redactor.widgets import RedactorEditor
from django import forms
from django.contrib import messages
from bibliocratie.gspread_to_json import GetGoogleSheetAsDict
import watson
from bibliocratie.models import *
from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.admin import UserAdmin


class SouscriptionHistoryInline(admin.TabularInline):
    model = SouscriptionHistory

class SouscriptionInline(admin.TabularInline):
    model = Souscription

class DiscountInline(admin.TabularInline):
    model = Discount

class CommandeHistoryInline(admin.TabularInline):
    model = CommandeHistory

class AdresseFactInline(admin.StackedInline):
    model = Adresse
    extra = 0
    exclude = ("type","client",)
    verbose_name = "Adresse de facturation"
    verbose_name_plural = "Adresse de facturation"

    def get_queryset(self, request):
        # get the existing query set, then empty it.
        qs = super(AdresseFactInline, self).get_queryset(request)
        return qs.filter(type='FACT')

    def has_add_permission(self, request):
        return False

class AdresseLivrInline(admin.StackedInline):
    model = Adresse
    extra = 0
    exclude = ("type","client",)
    verbose_name = "Adresse de livraison"
    verbose_name_plural = "Adresse de livraison"

    def get_queryset(self, request):
        # get the existing query set, then empty it.
        qs = super(AdresseLivrInline, self).get_queryset(request)
        return qs.filter(type='LIVR')

    def has_add_permission(self, request):
        return False

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    readonly_fields = ('client',)
    list_filter = ('etat',)
    search_fields = ('no_commande',)
    list_display = ('etat', 'no_commande', 'detail', 'client', 'pays_livraison','transaction_id')
    inlines = [
        SouscriptionInline,
        DiscountInline,
        AdresseFactInline,
        AdresseLivrInline,
        CommandeHistoryInline,
    ]


@admin.register(Souscription)
class SouscriptionAdmin(admin.ModelAdmin):
    raw_id_fields = ('panier','livre')
    inlines = [
        SouscriptionHistoryInline,
    ]

class AdresseUserInline(admin.StackedInline):
    model = Adresse
    extra = 0
    exclude = ("type","commande",)

    def get_queryset(self, request):
        # get the existing query set, then empty it.
        qs = super(AdresseUserInline, self).get_queryset(request)
        return qs.filter(type='CLIENT')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class UserPreferenceInline(admin.StackedInline):
    model = UserPreference

    def has_delete_permission(self, request, obj=None):
        return False

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = BiblioUser
        fields = ('email', )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField(label= ("Password"),
        help_text= ("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"password/\">this form</a>."))

    class Meta:
        model = BiblioUser
        fields = ('email', 'password', 'is_active')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

class BiblioUserAdmin(AdminImageMixin, UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm


    # readonly_fields = ('adresse','preference')
    fieldsets = (
        (None, {'fields': (
        'email', 'password', 'slug', 'biographie', 'avatar', 'username',
        'site_internet','lieu','pref_actu','pref_adol','pref_art','pref_bd','pref_beau','pref_cuisine','pref_dict','pref_droit',
        'pref_entreprise','pref_erotisme','pref_esoterisme','pref_etude','pref_famille','pref_fantaisie',
        'pref_histoire','pref_humour','pref_informatique','pref_litterature','pref_sentiment','pref_enfant',
        'pref_loisirs','pref_manga','pref_nature','pref_policier','pref_religion','pref_sciencefi','pref_sciencehu',
        'pref_sciencete','pref_scolaire','pref_sport','pref_tourisme','pref_photo')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    search_fields = ('email', 'username', 'id')
    list_display = ('email', 'username', 'is_staff','email')
    inlines = [
        AdresseUserInline,
        UserPreferenceInline
    ]

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )

admin.site.register(BiblioUser, BiblioUserAdmin)


class CommentaireInline(NestedTabularInline):
    model = Commentaire
    extra = 1
    raw_id_fields = ('user','livre')
    fk_name = "livre"
    def queryset(self,request):
        return self.get_queryset(request)

class VoteInline(NestedTabularInline):
    model = Vote
    extra = 1
    raw_id_fields = ('user','proposition')
    def queryset(self,request):
        return self.get_queryset(request)

class ImagePropositionInline(NestedTabularInline):
    fk_name = "livre"
    model = ImageProposition
    raw_id_fields = ('auteur','livre')
    extra = 1
    inlines = [
        VoteInline,
        ]
    def queryset(self,request):
        return self.get_queryset(request)

class NumberPropositionInline(NestedTabularInline):
    fk_name = "livre"
    extra = 1
    model = NumberProposition
    raw_id_fields = ('auteur','livre')
    inlines = [
        VoteInline,
        ]
    def queryset(self,request):
        return self.get_queryset(request)

class TextPropositionInline(NestedTabularInline):
    fk_name = "livre"
    model = TextProposition
    raw_id_fields = ('auteur','livre')
    extra = 1
    inlines = [
        VoteInline,
        ]
    def queryset(self,request):
        return self.get_queryset(request)

class CharPropositionInline(NestedTabularInline):
    fk_name = "livre"
    model = CharProposition
    raw_id_fields = ('auteur','livre')
    extra = 1
    inlines = [
        VoteInline,
        ]
    def queryset(self,request):
        return self.get_queryset(request)

class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        w = self.fields['auteurs'].widget
        choices = []
        for auteur in self.instance.auteurs.all():
            choices.append((auteur.id, unicode(auteur)))
        w.choices = choices

@admin.register(Livre)
class LivreAdmin(AdminImageMixin, watson.SearchAdmin):
    model = Livre
    list_display = ('titre', 'phase','pre_souscription','a_la_une','date_feedback','date_souscription','nb_souscripteurs')
    search_fields = ("titre",)
    list_filter = ('phase', 'is_active','a_la_une','pre_souscription')
    form = UserForm
    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        if 'phase' in form.changed_data:
            if form['phase'].value()=='VALIDATE' and float(form['prix_vente'].value())<0:
                messages.add_message(request, messages.INFO, 'Vous ne pouvez pas valider un livre qui a un prix negatif')
                return
        super(LivreAdmin, self).save_model(request, obj, form, change)


class VoteEtCommentairesLivre(Livre):
    class Meta:
        proxy = True


@admin.register(VoteEtCommentairesLivre)
class VoteAdmin(AdminImageMixin, NestedModelAdmin, watson.SearchAdmin):
    model = VoteEtCommentairesLivre
    fieldsets = (
        (None, {'fields': (
        'titre',)}),
    )
    search_fields = ("titre",)
    inlines = [
        CommentaireInline,
        NumberPropositionInline,
        CharPropositionInline,
        TextPropositionInline,
        ImagePropositionInline,
    ]
    def has_add_permission(self, request):
        return False

admin.site.register(DiscountCode)

admin.site.register(Tag)

class TarifsFournisseurAdmin(admin.ModelAdmin):
    actions = ['refresh_tarif']
    list_display = ['__str__','url_worksheet',]

    def url_worksheet(self,obj):
        link = "https://docs.google.com/spreadsheets/d/%s" % obj.sheet_key
        return '<a href="%s" target="blank">%s</a>' % (link, link)
    url_worksheet.allow_tags = True

    def refresh_tarif(self, request, queryset):
        for tarif in queryset:
            try:
                result_impression = GetGoogleSheetAsDict(user=settings.GOOGLE_ACCOUNT,password=settings.GOOGLE_PASSWORD,sheet=tarif.sheet_key,worksheet=tarif.worksheet_impression)
                result_expedition = GetGoogleSheetAsDict(user=settings.GOOGLE_ACCOUNT,password=settings.GOOGLE_PASSWORD,sheet=tarif.sheet_key,worksheet=tarif.worksheet_expedition)

                if result_impression['error']:
                    self.message_user(request, result_impression['message'],level=messages.ERROR)
                elif result_expedition['error']:
                    self.message_user(request, result_expedition['message'],level=messages.ERROR)
                else:
                    tarif.tarifs_impression=result_impression['data']
                    tarif.tarifs_expedition=result_expedition['data']
                    tarif.save()
                    self.message_user(request, "les tarifs de %s ont bien ete raffraichis" % tarif,level=messages.INFO)
            except Exception as e:
                self.message_user(request, str(e.__class__) + e.message,level=messages.ERROR)

    refresh_tarif.short_description = "Raffraichir les tarifs fournisseurs"

admin.site.register(TarifsFournisseur, TarifsFournisseurAdmin)

class TarifsExpeditionAdmin(admin.ModelAdmin):
    actions = ['refresh_tarif']
    list_display = ['__str__','url_worksheet',]

    def url_worksheet(self,obj):
        link = "https://docs.google.com/spreadsheets/d/%s" % obj.sheet_key
        return '<a href="%s" target="blank">%s</a>' % (link, link)
    url_worksheet.allow_tags = True

    def refresh_tarif(self, request, queryset):
        for tarif in queryset:
            try:
                result = GetGoogleSheetAsDict(user=settings.GOOGLE_ACCOUNT,password=settings.GOOGLE_PASSWORD,sheet=tarif.sheet_key,worksheet=tarif.worksheet)
                if result['error']:
                    self.message_user(request, result['message'],level=messages.ERROR)
                else:
                    tarif.tarifs=result['data']
                    tarif.save()
                    self.message_user(request, "les tarifs de %s ont bien ete raffraichis" % tarif,level=messages.INFO)
            except Exception as e:
                self.message_user(request, str(e.__class__) + e.message,level=messages.ERROR)

    refresh_tarif.short_description = "Raffraichir les tarifs expedition"


admin.site.register(TarifsExpedition, TarifsExpeditionAdmin)


class TimelineCommentaireInline(admin.TabularInline):
    model = TimelineCommentaire
    raw_id_fields = ('user',)

class PartageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PartageForm, self).__init__(*args, **kwargs)
        w = self.fields['partage'].widget
        choices = []
        for share in self.instance.partage.all():
            choices.append((share.id, unicode(share)))
        w.choices = choices

@admin.register(Timeline)
class TimeLineAdmin(admin.ModelAdmin):
    raw_id_fields = ('user','content_type')
    inlines = [
        TimelineCommentaireInline,
    ]
    form = PartageForm

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    raw_id_fields = ('qui','suit')

@admin.register(MeRappeler)
class MeRappelerAdmin(admin.ModelAdmin):
    pass

@admin.register(DemanderNewSouscription)
class DemanderNewSouscriptionAdmin(admin.ModelAdmin):
    pass

@admin.register(UrlIndex)
class UrlIndexAdmin(admin.ModelAdmin):
    pass

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    raw_id_fields = ('user','livre')

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    raw_id_fields = ('user','livre')
    list_display = ('user', 'livre','contenu', 'date')
    search_fields = ('livre__titre','user__email','user__username')


@admin.register(TimelineCommentaire)
class TimelineCommentaireAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_display = ('user', 'contenu','date')
    search_fields = ('user__email','user__username')
