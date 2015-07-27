# -*- coding: utf-8 -*-
import json
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import MultiValueDictKeyError
from django.http import Http404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.views import redirect_to_login
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
import dateutil.parser
import calendar
from decimal import *

from djangular.views.mixins import JSONResponseMixin, allow_remote_invocation
from djangular.views.crud import NgCRUDView
from rest_framework import viewsets
from rest_framework import filters
import django_filters
import watson

from bibliocratie.forms import *
from bibliocratie.serializers import *
from bibliocratie.receiver import *

logger = logging.getLogger(__name__)
REDIRECT_FIELD_NAME = 'next'


class HomeView(FormView):
    template_name = 'bibliocratie/vitrine.html'
    form_class = BibliocratieAuthenticationForm
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('profil_detail',kwargs={'slug':request.user.slug}))
        return super(HomeView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        try:
            next = self.request.GET['next']
        except:
            next = None
        context.update(
            next = next,
            today = timezone.now(),
            lancement_form = LancementForm(),
        )
        return context

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        return super(HomeView, self).post(request, **kwargs)

    def ajax(self, request):
        if request.FILES.has_key('avatar'):
            request.FILES.keys().index('avatar')
            user_form = BiblioUserFileForm(request.POST, request.FILES, instance=request.user)
            if user_form.is_valid():
                obj = user_form.save()
            response_data = {'errors': None, 'success_url': None}
            return HttpResponse(json.dumps(response_data), content_type="application/json")


        data = json.loads(request.body)
        if data['action']=='login':
            form = BibliocratieAuthenticationForm(data=data)
        elif data['action']=='signup':
            form = BibliocratieSignupForm(data=data)
        elif data['action']=='recover':
            form = BibliocratieRecoverForm(data=data)
        elif data['action']=='biolieu':
            form = BiblioUserPrefForm(data=data, instance=request.user)
        elif data['action']=='adresse':
            form = AdresseForm(data=data, instance=request.user.adresse)
        if form.is_valid():
            if data['action']=='biolieu' or data['action']=='adresse':
                form.save()
            elif data['action']=='signup' and data.has_key('need_more_info') and data['need_more_info']==True:
                user = form.get_user()
                user.need_more_info=True
                user.save()

            if data['action'] in ['login','signup']:
                panier=Commande.objects.getUserPanier(request)
                auth_login(self.request, form.get_user())
                panier_apres=Commande.objects.getUserPanier(request)
                if panier.pk!=None:
                    panier_apres.save()
                    panier_apres.copy(panier)
                    panier.delete()
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
        next_page = data.get('next')
        if not next_page:
            try:
                next_page = reverse('profil_detail', args=[request.user.slug])
            except:
                next_page =None

        # try:
        #     next_page = parse_qs(urlnextparam).values()[0][0]
        # except:
        #     try:
        #         next_page = reverse('profil_detail', args=[request.user.slug])
        #     except:
        #         next_page = None

            # next_page = request.META.get('HTTP_REFERER')
        # next_page=settings.LOGIN_REDIRECT_URL
        # if (REDIRECT_FIELD_NAME in request.POST or
        # REDIRECT_FIELD_NAME in request.GET):
        # next_page = request.POST.get(REDIRECT_FIELD_NAME,
        # request.GET.get(REDIRECT_FIELD_NAME))
        # Security check -- don't allow redirection to a different host.
        # if not is_safe_url(url=next_page, host=request.get_host()):
        # next_page = request.path
        # response_data = {'errors': form.errors, 'success_url': force_text(next_page)}
        response_data = {'errors': form.errors, 'success_url': next_page}
        return HttpResponse(json.dumps(response_data), content_type="application/json")


    @method_decorator(sensitive_post_parameters('password'))
    def dispatch(self, request, *args, **kwargs):
        request.session.set_test_cookie()
        return super(HomeView, self).dispatch(request, *args, **kwargs)


class LoginView(HomeView):
    template_name = 'registration/login.html'


class SigninView(HomeView):
    def get_template_names(self):
        return ['registration/signin.html']


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL)

class ContactView(FormView):
    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        return super(HomeView, self).post(request, **kwargs)

    def ajax(self, request):
        try:
            data = json.loads(request.body)
        except:
            data={}
        form = ContactForm(data=data)
        if form.is_valid():
            subject = _("Nouveau message d'un utilisateur")
            to = ['contact@example.com']
            ctx={
                    'email': form.cleaned_data['mail'],
                    'prenom' : form.cleaned_data['prenom'],
                    'nom' : form.cleaned_data['nom'],
                    'telephone': form.cleaned_data['telephone'],
                    'message' : form.cleaned_data['message']
            }

            message = get_template('mails/contact.html').render(Context(ctx))
            msg = EmailMessage(subject, message, to=to)
            msg.content_subtype = 'html'
            msg.send()
        response_data = {'errors': form.errors}
        return HttpResponse(json.dumps(response_data), content_type="application/json")


class ProfilView(DetailView):
    template_name = 'bibliocratie/profil.html'
    model = BiblioUser

    def get_context_data(self, **kwargs):
        context = super(ProfilView, self).get_context_data(**kwargs)
        user = self.get_object()
        context.update(
            user_form=BiblioUserForm(instance=user),
            adresse_form_fact=AdresseForm(auto_id=u'id1_%s', form_name='facturation_form',scope_prefix="facturation_data",instance=user.adresse),
            preference_form = PreferenceForm(instance=user.userpreference),
        )
        return context

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        user_form = None
        facturation_form = None
        livraison_form = None
        preference_form = None
        old_slug=self.get_object().slug
        if request.FILES.has_key('avatar'):
            request.FILES.keys().index('avatar')
            user_form = BiblioUserFileForm(request.POST, request.FILES, instance=self.get_object())
            if user_form.is_valid():
                obj = user_form.save()
            return HttpResponse(json.dumps({}), content_type="application/json")
        else:
            data=json.loads(request.body)
            user = self.get_object()
            if data.has_key('preference_data'):
                preference_form = PreferenceForm(data=data["preference_data"],instance=user.userpreference)
                if preference_form.is_valid():
                    obj = preference_form.save()
            if data.has_key('facturation_data'):
                facturation_form = AdresseForm(data=data["facturation_data"],instance=user.adresse)
                if facturation_form.is_valid():
                    obj = facturation_form.save()
            if data.has_key('biblio_user_data'):
                user_form = BiblioUserForm(data=data["biblio_user_data"],instance=user)
                if user_form.is_valid():
                    obj = user_form.save()
        response_data = {
            'biblio_user_errors':user_form.errors if user_form else None,
            'facturation_errors':facturation_form.errors if facturation_form else None,
            'preference_errors':preference_form.errors if preference_form else None,
            'refresh':old_slug!=user.slug,
            'new_url':reverse('profil_detail',kwargs={'slug' : user.slug})

        }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

class MembresView(TemplateView):
    template_name = 'bibliocratie/membres.html'

class PlayView(TemplateView):
    template_name = 'bibliocratie/play.html'

class AideView(TemplateView):
    template_name = 'bibliocratie/aide.html'

class PourquoiBibliocratieView(TemplateView):
    template_name = 'bibliocratie/pourquoi_bibliocratie.html'

class ModeEmploiView(TemplateView):
    template_name = 'bibliocratie/mode_emploi.html'

class ConfidentialiteView(TemplateView):
    template_name = 'bibliocratie/confidentialite.html'

class SecuriteView(TemplateView):
    template_name = 'bibliocratie/securite.html'

class CGUView(TemplateView):
    template_name = 'bibliocratie/cgu.html'

class LancementView(TemplateView):
    template_name = 'bibliocratie/lancement.html'
    model = Livre

    def get(self, request, *args, **kwargs):
        return super(LancementView, self).get(request, *args, **kwargs)

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        data=json.loads(request.body)
        form = LancementForm(data=data)
        if form.is_valid():
            obj = form.save()
        response_data = {
            'errors':form.errors,
            'success_url': reverse('lancement_debut', args=[obj.slug]) if form.is_valid() else None,
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(LancementView, self).get_context_data(**kwargs)
        context.update(
            form=LancementForm(),
        )
        return context


class LancementDebutView(DetailView):
    template_name = 'bibliocratie/lancement_debut.html'
    model = Livre

    def get(self, request, *args, **kwargs):
        livre = self.get_object()
        # if not request.user.is_authenticated():
        #     return redirect_to_login(next=reverse('lancement_debut', args=[self.get_object().slug]))
        if livre.auteurs.all().count()==0:
            livre.auteurs.add(self.request.user)
            livre.save()
        #le livre a cette etape n'est consultable que par le staff, et les auteurs et le owner
        if request.user in livre.auteurs.all():
            return super(LancementDebutView, self).get(request, *args, **kwargs)
        else:
            raise Http404

    def post(self, request, **kwargs):
        if not request.user.is_authenticated():
            return redirect_to_login(next=reverse('lancement_debut', args=[self.get_object().slug]))
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        success_url = None
        form_errors = {}
        data=json.loads(request.body)
        data['category']=data['categorie']['value']
        data['genre']=data['genre']['value']
        data['type_encre']=data['couleur']['value']

        form = LancementDebutForm(data=data, instance=self.get_object())

        if form.is_valid():
            obj = form.save(commit=False)
            for tag in obj.tags.all():
                obj.tags.remove(tag)
            for tag_name in data['tags']:
                tag, created = Tag.objects.get_or_create(text = tag_name['text'].lower())
                if obj.tags.filter(text=tag.text).count()==0:
                    obj.tags.add(tag)

            errors = []

            if obj.category=="" :
                errors.append(force_text(_("La categorie n'a pas ete renseignee")))
            if obj.genre=='':
                errors.append(force_text(_("Le genre n'a pas ete renseigne")))
            if obj.type_encre=='':
                errors.append(force_text(_("Le type d'encre n'a pas ete renseigne")))
            if obj.tags.count()==0:
                errors.append(force_text(_("Aucun tag n'a ete renseigne")))

            if len(errors):
                form_errors = {'__all__': errors}
            else:
                next=data['next']
                obj.lancement_debut_valide=True;
                obj.lancement_interieur_valide=False;
                obj.lancement_couverture_valide=False;
                obj.lancement_prixdate_valide=False;
                obj.lancement_fin_valide=False;
                if not obj.maquette:
                    obj.format='CST'
                else:
                    obj.format='NTS'
                obj.save()
                if next:
                    success_url=reverse('lancement_interne', args=[obj.slug])
        else:
            form_errors=form.errors
        response_data = {
            'errors':form_errors,
            'success_url':success_url,
            }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(LancementDebutView, self).get_context_data(**kwargs)
        lancement_debut_form=LancementDebutForm(instance=self.get_object())
        genre_list = []
        categorie_list = []
        couleur_list = []
        for genre in lancement_debut_form.fields['genre'].choices:
            genre_list.append({'value':genre[0],'display':genre[1].title()})
        for categorie in lancement_debut_form.fields['category'].choices:
            categorie_list.append({'value':categorie[0],'display':categorie[1].title()})
        for couleur in lancement_debut_form.fields['type_encre'].choices:
            couleur_list.append({'value':couleur[0],'display':couleur[1].title()})

        object = self.get_object()

        context.update(
            lancement_debut_form=lancement_debut_form,
            genre_list=json.dumps(SelectSerializer(genre_list,many=True).data),
            categorie_list=json.dumps(SelectSerializer(categorie_list,many=True).data),
            couleur_list=json.dumps(SelectSerializer(couleur_list,many=True).data),
            categorie=json.dumps(SelectSerializer({'value':object.category,'display':object.get_category_display()}).data),
            genre=json.dumps(SelectSerializer({'value':object.genre,'display':object.get_genre_display()}).data),
            couleur=json.dumps(SelectSerializer({'value':object.type_encre,'display':object.get_type_encre_display()}).data),
            maquette=object.maquette,
            couverture=object.couverture,
            pre_souscription=object.pre_souscription,
            tags = json.dumps(TagSerializer(self.get_object().tags,many=True).data),
        )
        return context

class LancementInterneView(DetailView):
    template_name = 'bibliocratie/lancement_interne.html'
    model = Livre

    def get(self, request, *args, **kwargs):
        livre = self.get_object()
        if not livre.lancement_debut_valide:
            return HttpResponseRedirect(reverse('lancement_debut',kwargs={'slug':livre.slug}))
        #le livre a cette etape n'est consultable que par les auteurs
        if request.user in livre.auteurs.all():
            return super(LancementInterneView, self).get(request, *args, **kwargs)
        else:
            raise Http404

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        error = False
        success_url = None
        form_errors = {}
        if request.FILES.has_key('fichier_auteur'):
            form = LancementFichiersForm(request.POST, request.FILES, instance=self.get_object())
            if form.is_valid():
                obj = form.save()

        else:
            data=json.loads(request.body)
            form = LancementInterneForm(data=data, instance=self.get_object())
            if form.is_valid():
                obj = form.save(commit=False)
                errors = form._errors.setdefault(forms.forms.NON_FIELD_ERRORS, forms.util.ErrorList())

                if not hasattr(obj.fichier_auteur,'url'):
                    errors.append(force_text(_("le fichier auteur n'est pas present")))
                    error = True

                if obj.type_encre=='COL':
                    if not obj.nb_pages_couleur:
                        form._errors['nb_pages_couleur'] = [force_text(_("Vous devez renseigner le nombre de pages en couleur"))]
                        error = True

                    if obj.nb_pages_nb==None:
                        form._errors['nb_pages_nb'] = [force_text(_("Vous devez renseigner le nombre de pages noir et blanc"))]
                        error = True

                    if obj.nb_pages_couleur and obj.nb_pages_nb:
                        obj.nb_pages=obj.nb_pages_couleur + obj.nb_pages_nb
                else:
                    #Cas du noir et blanc
                    if not obj.maquette: #L'auteur fait sa maquette
                        if obj.nb_pages==None:
                            form._errors['nb_pages'] = [force_text(_("Vous devez renseigner le nombre de pages de votre livre"))]
                            error = True
                        else:
                            if obj.nb_pages<16:
                                form._errors['nb_pages'] = [force_text(_("Le nombre de pages de votre maquete ne peut etre inferieur a 16"))]
                                error = True

                    else: #Bibliocratie fait la maquette
                        if obj.nb_carac:
                            if obj.nb_carac<3291:
                                form._errors['nb_carac'] = [force_text(_("Le nombre de caracteres doit etre superieur a 3291"))]
                                error = True
                        else:
                            form._errors['nb_carac'] = [force_text(_("Vous devez renseigner le nombre de caracteres de votre livre"))]
                            error = True

                        if obj.nb_chapitres==None:
                            form._errors['nb_chapitres'] = [force_text(_("Vous devez renseigner le nombre de chapitres (0 si aucun)"))]
                            error = True
                        elif obj.nb_chapitres<0:
                            form._errors['nb_chapitres'] = [force_text(_("Votre nombre de chapitre est negatif, ce n'est pas normal"))]
                            error = True


                        #calcul du nombre de pages
                        if obj.format=='FM1':
                            obj.nb_pages = math.ceil(obj.nb_chapitres*0.9+obj.nb_carac/860)
                            obj.nb_pages = obj.nb_pages + obj.nb_pages % 2
                        elif obj.format=='FM2':
                            obj.nb_pages = math.ceil(obj.nb_chapitres*1.2+obj.nb_carac/1070)
                            obj.nb_pages = obj.nb_pages + obj.nb_pages % 2
                        elif obj.format=='FM3':
                            obj.nb_pages = math.ceil(obj.nb_chapitres*0.7+obj.nb_carac/1600)
                            obj.nb_pages = obj.nb_pages + obj.nb_pages % 2

                if obj.format=='CST':
                    if obj.largeur_mm<100:
                        form._errors['largeur_mm'] = [force_text(_("La largeur de votre livre ne peut etre inferieure a 100"))]
                        error = True

                    if obj.hauteur_mm<100:
                        form._errors['hauteur_mm'] = [force_text(_("La hauteur de votre livre ne peut etre inferieure a 100"))]
                        error = True

                if obj.format=='NTS':
                    form._errors['format'] = [force_text(_("Vous n'avez pas choisi de format"))]
                    error = True

                if not error:
                    next=data['next']
                    obj.lancement_interieur_valide=True;
                    obj.lancement_couverture_valide=False;
                    obj.lancement_prixdate_valide=False;
                    obj.lancement_fin_valide=False;
                    obj.save()
                    if next:
                        success_url=reverse('lancement_couverture', args=[obj.slug])
            else:
                error=True
        response_data = {
            'errors':form.errors if error else {},
            'success_url':success_url,
            }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(LancementInterneView, self).get_context_data(**kwargs)
        context.update(
            form=LancementInterneForm(instance=self.get_object()),
            formfichier=LancementFichiersForm(instance=self.get_object())
        )
        return context

class LancementCouvertureView(DetailView):
    template_name = 'bibliocratie/lancement_couverture.html'
    model = Livre

    def get(self, request, *args, **kwargs):
        livre = self.get_object()
        if not livre.lancement_interieur_valide:
            return HttpResponseRedirect(reverse('lancement_interne',kwargs={'slug':livre.slug}))
        #le livre a cette etape n'est consultable que les auteurs
        if request.user in livre.auteurs.all():
            return super(LancementCouvertureView, self).get(request, *args, **kwargs)
        else:
            raise Http404

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        success_url = None
        form_errors = {}
        if request.FILES.has_key('image_couverture') or request.FILES.has_key('maquete_couverture'):
            form = LancementFichiersForm(request.POST, request.FILES, instance=self.get_object())
            if form.is_valid():
                obj = form.save()
        else:
            data=json.loads(request.body)
            form = LancementCouvertureForm(data=data, instance=self.get_object())

            if form.is_valid():
                obj = form.save(commit=False)
                errors = []

                if not hasattr(obj.image_couverture,'url'):
                    errors.append(force_text(_("le fichier image de la couverture n'est pas present")))

                if not obj.couverture:
                    if not hasattr(obj.maquete_couverture,'url'):
                        errors.append(force_text(_("le fichier maquete de la couverture n'est pas present")))

                if obj.couverture and obj.modele_couverture=='':
                    errors.append(force_text(_("Vous devez choisir un modele de couverture")))

                if len(errors):
                    form_errors = {'__all__': errors}
                else:
                    next=data['next']
                    obj.lancement_couverture_valide=True;
                    obj.lancement_prixdate_valide=False;
                    obj.lancement_fin_valide=False;
                    obj.save()
                    if next:
                        success_url=reverse('lancement_prixdate', args=[obj.slug])
            else:
                form_errors=form.errors
        response_data = {
            'errors':form_errors,
            'success_url':success_url,
            }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(LancementCouvertureView, self).get_context_data(**kwargs)
        context.update(
            form=LancementCouvertureForm(instance=self.get_object()),
            formfichier=LancementFichiersForm(instance=self.get_object())
        )
        return context

class LancementPrixdateView(DetailView):
    template_name = 'bibliocratie/lancement_prixdate.html'
    model = Livre

    def get(self, request, *args, **kwargs):
        livre = self.get_object()
        if not livre.lancement_couverture_valide:
            return HttpResponseRedirect(reverse('lancement_couverture',kwargs={'slug':livre.slug}))
        #le livre a cette etape n'est consultable que par le staff, et les auteurs et le owner
        if request.user in livre.auteurs.all():
            return super(LancementPrixdateView, self).get(request, *args, **kwargs)
        else:
            raise Http404


    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        success_url = None
        data=json.loads(request.body)
        form = LancementPrixDateForm(data=data, instance=self.get_object())
        if form.is_valid():
            obj = form.save(commit=False)
            errors = []
            cout_production = obj.cout_production
            if cout_production<obj.get_cout_production()['prix_exemplaire']:
                errors.append(force_text(_("Le prix de production ne peut etre inferieur a ")+ str(cout_production)))

            if cout_production==None:
                obj.prix_vente=-1

            if len(errors):
               form_errors = {'__all__': errors}
            else:
                #les campagnes se terminent le soir!
                form_errors=form.errors
                next=data['next']
                if obj.pre_souscription and obj.date_feedback:
                    obj.date_souscription=obj.date_feedback + relativedelta(weeks=+2)
                if obj.pre_souscription:
                    obj.date_fin_presouscription= obj.date_souscription+relativedelta(weekday=MO(-1))

                obj.lancement_prixdate_valide=True;
                obj.lancement_fin_valide=False;
                obj.save()
                if next:
                    success_url=reverse('lancement_fin', args=[obj.slug])
        else:
            form_errors=form.errors
        response_data = {
            'errors':form_errors,
            'success_url':success_url,
            }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(LancementPrixdateView, self).get_context_data(**kwargs)
        instance=self.get_object()
        #la souscription se termine le soir, on affiche donc la date de la veille.
        if instance.nb_jours_campagne:
            instance.nb_jours_campagne-=1
        form=LancementPrixDateForm(instance=instance)

        context.update(
            form=form,
        )
        return context


class LancementVousView(DetailView):
    template_name = 'bibliocratie/lancement_vous.html'
    model = Livre
    def get(self, request, *args, **kwargs):
        livre = self.get_object()
        if not livre.lancement_prixdate_valide:
            return HttpResponseRedirect(reverse('lancement_prixdate',kwargs={'slug':livre.slug}))
        #le livre a cette etape n'est consultable que par le staff, et les auteurs et le owner
        if request.user in livre.auteurs.all():
            return super(LancementVousView, self).get(request, *args, **kwargs)
        else:
            raise Http404

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        data=json.loads(request.body)
        user_form = BiblioUserBiolieu(instance=self.request.user, data=data['biblio_user_data'])
        adresse_form = AdresseForm(instance=self.request.user.adresse, data=data['adresse_data'])
        if user_form.is_valid() and adresse_form.is_valid():

            user = user_form.save()
            adresse = adresse_form.save()
            error = False
            errors = []
            if not user.biographie:
                user_form._errors['biographie'] = [force_text(_("Vous devez renseigner votre biographie"))]
                error = True
                errors.append(force_text(_("Vous devez renseigner votre biographie")))
            if not user.lieu:
                user_form._errors['lieu'] = [force_text(_("Vous devez renseigner un lieu"))]
                errors.append(force_text(_("Vous devez renseigner un lieu")))
                error = True
            if not user.avatar:
                user_form._errors['avatar'] = [force_text(_("Vous devez uploader un avatar"))]
                errors.append(force_text(_("Vous devez uploader un avatar")))
                error = True
            if not error:
                obj = self.get_object()
                obj.lancement_vous_valide=True
                obj.biographie=user.biographie
                obj.save()
            else:
                user_form.errors['__all__'] = errors

        response_data = {
            'user_form_errors' : user_form.errors,
            'adresse_form_errors' : adresse_form.errors,
            'success_url' : reverse('livre_detail', args=[self.get_object().slug]) if user_form.is_valid() else None,
            }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(LancementVousView, self).get_context_data(**kwargs)
        context.update(
            user_form = BiblioUserBiolieu(instance=self.request.user),
            adresse_form = AdresseForm(instance=self.request.user.adresse)
        )
        return context


class LancementFinView(DetailView):
    template_name = 'bibliocratie/lancement_fin.html'
    model = Livre

    def get(self, request, *args, **kwargs):
        livre = self.get_object()
        if not livre.lancement_vous_valide:
            return HttpResponseRedirect(reverse('lancement_vous',kwargs={'slug':livre.slug}))
        #le livre a cette etape n'est consultable que par le staff, et les auteurs et le owner
        if request.user in livre.auteurs.all():
            return super(LancementFinView, self).get(request, *args, **kwargs)
        else:
            raise Http404

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        data=json.loads(request.body)
        form = LancementFinForm(data=data, instance=self.get_object())
        if form.is_valid():
            obj = form.save(commit=False)
            obj.lancement_fin_valide=True
            obj.save()
        response_data = {
            'errors':form.errors,
            'success_url':reverse('livre_detail', args=[obj.slug]) if form.is_valid() else None,
            }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(LancementFinView, self).get_context_data(**kwargs)
        context.update(
            form=LancementFinForm(instance=self.get_object()),
        )
        return context

class NotificationsView(TemplateView):
    template_name = 'bibliocratie/notifications_fullpage.html'

class LivreList(TemplateView):
    template_name = 'bibliocratie/livre_list.html'

class PresouscriptionList(TemplateView):
    template_name = 'bibliocratie/presouscription_list.html'

class LivreDetail(DetailView):
    model = Livre
    def is_editable(self):
        # Détermine si le bouton edit est affiché
        if self.object.phase in ['CREATION','VALIDATE','CREATRAN','GETMONEY']:
            #En creation seuls les auteurs et le staff ont accès au livre
            if (self.request.user in self.object.auteurs.all()):
                return {
                    "general":True,
                    "type_titres":True,
                    "type_prix":True,
                    "type_couvertures":True,
                    "type_extraits":True,
                    "type_biographies":True
                       }
        if self.object.phase in ['FEEDBACK']:
            #En creation seuls les auteurs et le staff ont accès au livre
            if (self.request.user in self.object.auteurs.all()):
                return {
                    "general":True,
                    "type_titres":True if self.object.type_titres=='NEVER_OPENED' else False,
                    "type_prix":True if self.object.type_prix=='NEVER_OPENED' else False,
                    "type_couvertures":True if self.object.type_couvertures=='NEVER_OPENED' else False,
                    "type_extraits":True if self.object.type_extraits=='NEVER_OPENED' else False,
                    "type_biographies":True if self.object.type_biographies=='NEVER_OPENED' else False,
                       }
        return {
                "general":False,
                "type_titres":False,
                "type_prix":False,
                "type_couvertures":False,
                "type_extraits":False,
                "type_biographies":False
                }

    def is_sondageable(self):
        # Détermine si le bouton sondage edit est affiché
        if self.object.phase in ['CREATION','CREATRAN']:
            if (self.request.user in self.object.auteurs.all()):
                return {
                    "type_titres":True,
                    "type_prix":True,
                    "type_couvertures":True,
                    "type_extraits":True,
                    "type_biographies":True
                       }
        if self.object.phase == 'FEEDBACK':
            if (self.request.user in self.object.auteurs.all()):
                return {
                    "type_titres":True if self.object.type_titres=='NEVER_OPENED' else False,
                    "type_prix":True if self.object.type_prix=='NEVER_OPENED' else False,
                    "type_couvertures":True if self.object.type_couvertures=='NEVER_OPENED' else False,
                    "type_extraits":True if self.object.type_extraits=='NEVER_OPENED' else False,
                    "type_biographies":True if self.object.type_biographies=='NEVER_OPENED' else False,
                       }
        return {
                "general":False,
                "type_titres":False,
                "type_prix":False,
                "type_couvertures":False,
                "type_extraits":False,
                "type_biographies":False
                }

    def is_proposable(self):
        if self.object.phase in ['CREATION','FEEDBACK','CREATRAN']:
            return True
        return False

    def is_presouscription_transform(self):
        if self.object.phase=='CREA-FEE' and self.request.user in self.object.auteurs.all():
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super(LivreDetail, self).get_context_data(**kwargs)
        self.object = self.get_object()
        try:
            user_rating = Rating.objects.get(livre = self.object, user=self.request.user).rating
        except:
            user_rating = 0

        if self.object.phase=='CREA-FEE':
            if self.request.user not in self.object.auteurs.all():
                if self.object.type_titres=='OPEN':
                    self.object.type_titres='READ_ONLY'
                if self.object.type_prix=='OPEN':
                    self.object.type_prix='READ_ONLY'
                if self.object.type_extraits=='OPEN':
                    self.object.type_extraits='READ_ONLY'
                if self.object.type_couvertures=='OPEN':
                    self.object.type_couvertures='READ_ONLY'
                if self.object.type_biographies=='OPEN':
                    self.object.type_biographies='READ_ONLY'

        if self.request.user.is_authenticated():
            recommendation_livre =self.request.user.recommendation_livre(livre = self.object)
        else:
            user,created = BiblioUser.objects.get_or_create(email='anonyme@anonyme.com', username='anonyme', is_active=False)
            recommendation_livre=user.recommendation_livre(livre = self.object)

        is_buyer=self.request.user.is_authenticated() and (Livre.objects.filter(souscription__panier__client=self.request.user).filter(id=self.object.id).count()>0)

        context.update(
            image_form=ImagePropositionForm(),
            number_form=NumberPropositionForm(),
            text_form=TextPropositionForm(data={'valeur':""}),
            char_form=CharPropositionForm(),
            livre_form=LivreForm(instance=self.object),
            commentaire_form=CommentaireForm(),
            editable=self.is_editable(),
            sondageable=self.is_sondageable(),
            tags = json.dumps(TagSerializer(self.object.tags,many=True).data),
            user_rating = user_rating,
            presouscription_transform = self.is_presouscription_transform(),
            recommendation_livre = recommendation_livre,
            is_buyer = is_buyer > 0,
        )
        return context

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()
        if not self.object.is_active:
            raise Http404;

        if self.object.phase in ['CREATION','FROZEN','VALIDATE']:
            #En creation seuls les auteurs et le staff ont accès au livre
            if request.user.is_anonymous():
                return HttpResponseRedirect(reverse('signin')+'?next='+reverse('livre_detail', args=[self.object.slug]))

            if request.user not in self.object.auteurs.all():
                raise Http404("Le livre demande n'existe pas")
            #Si le debut n'est pas valide il faut le valider
            if not self.object.lancement_debut_valide:
                return HttpResponseRedirect(reverse('lancement_debut',kwargs={'slug':self.object.slug}))
            #Si la fin n'est pas valide il faut la valider
            if not self.object.lancement_fin_valide:
                return HttpResponseRedirect(reverse('lancement_fin',kwargs={'slug':self.object.slug}))

        if self.object.phase in ['CREATION','FROZEN','VALIDATE','FEEDBACK','CREA-FEE']:
            if self.object.pre_souscription:
                self.template_name = 'bibliocratie/presouscription_detail.html'
            else:
                self.template_name = 'bibliocratie/livre_detail.html'

        if self.object.phase in ['GETMONEY','CREATRAN','FROZ-FEE']:
            self.template_name = 'bibliocratie/livre_detail.html'

        elif self.object.phase=='SUCCES':
            self.template_name = 'bibliocratie/livre_detail_succes.html'
        elif self.object.phase=='ECHEC':
            self.template_name = 'bibliocratie/livre_detail_echec.html'
        elif self.object.phase=='CANCELLE':
            raise Http404("Le livre demande n'existe pas")

        logger.debug("fin de get LivreDetail : " + self.object.slug)
        return super(LivreDetail,self).get(request, *args, **kwargs)


    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, **kwargs):
        if request.is_ajax():
            self.object = self.get_object()
            return self.ajax(request)
        raise Http404;


    def ajax(self, request):
        if not request.user.is_authenticated():
            response_data = {
                    'errors': {'__all__': [force_text(_("Vous devez etre authentifie pour soumettre des donnees"))]},
                }
            return HttpResponse(json.dumps(response_data), content_type="application/json")


        if self.is_editable()['type_extraits']:
            if request.FILES.has_key('extrait1_img') or request.FILES.has_key('extrait2_img') or \
               request.FILES.has_key('extrait3_img') or request.FILES.has_key('extrait4_img') or request.FILES.has_key('image_couverture'):
                form = LivreFileForm(data=request.POST, files=request.FILES, instance=self.get_object())
                if form.is_valid():
                    obj = form.save()
                    response_data = {}
                    return HttpResponse(json.dumps(response_data), content_type="application/json")
                else:
                    response_data = {'error':form.errors}
                    return HttpResponse(json.dumps(response_data), content_type="application/json")
                raise Http404

        if request.POST.has_key('image_type'):
            if self.is_proposable() or self.is_presouscription_transform():
                #L'utilisateur a posté une proposition d'image
                form = ImagePropositionForm(request.POST, request.FILES)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.auteur=request.user
                    obj.livre=self.get_object()
                    if request.POST['image_type']=='extrait':
                        obj.type='EXTRA'
                    else:
                        obj.type='COVER'
                    if self.is_presouscription_transform():
                        #quand la presouscription se transforme en souscription, les propositions de l'auteurs sont automatiquement choisies
                        obj.private=True
                        obj.choisir()
                    obj.save()
                    response_data = {}
                    return HttpResponse(json.dumps(response_data), content_type="application/json")
                else:
                    response_data = {'error':form.errors}
                    return HttpResponse(json.dumps(response_data), content_type="application/json")
                raise Http404
            else:
                response_data = {
                    'errors': {'__all__': [u"le livre n'est pas ouvert aux propositions. Veuillez enregistrer vos modifications."]},
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")


        data=json.loads(request.body)
        if data.has_key("commentaire"):
            form = CommentaireForm(data=data['commentaire'])
            if form.is_valid():
                obj = form.save(commit=False)
                obj.user = request.user
                if self.object.phase=="SUCCES":
                    obj.avis_lecture = True
                else:
                    obj.avis_lecture = False
                try:
                    obj.reponse_a=Commentaire.objects.get(id=data['reply_to'])
                except:
                    obj.reponse_a=None
                obj.livre=self.get_object()
                obj.save()
            response_data = {
                'livre': LivreApiSerializer(self.get_object(), context={'request': self.request}).data,
                'errors': form.errors,
            }
            return HttpResponse(json.dumps(response_data), content_type="application/json")

        if data.has_key("type_proposition"):
            error = None
            if data['type_proposition']=='TITRE':
                if self.object.type_titres=="OPEN" or request.user in self.object.auteurs.all():
                    form = CharPropositionForm(data=data['proposition'])
                else:
                    error = _("le livre n'est pas ouvert aux propositions TITRE.")

            if data['type_proposition']=='PHRASE':
                if self.object.type_phrases=="OPEN" or request.user in self.object.auteurs.all():
                    form = CharPropositionForm(data=data['proposition'])
                else:
                    error = _("le livre n'est pas ouvert aux propositions PHRASE.")

            if data['type_proposition']=='EXTRA':
                if self.object.type_extraits=="OPEN" or request.user in self.object.auteurs.all():
                    form = TextPropositionForm(data=data['proposition'])
                else:
                    error = _("le livre n'est pas ouvert aux propositions EXTRA.")

            if data['type_proposition']=='BIO':
                if self.object.type_biographies=="OPEN" or request.user in self.object.auteurs.all():
                    form = TextPropositionForm(data=data['proposition'])
                else:
                    error = _("le livre n'est pas ouvert aux propositions BIO.")

            if data['type_proposition']=='PRIX':
                if self.object.type_prix=="OPEN" or request.user in self.object.auteurs.all():
                    form = NumberPropositionForm(data=data['proposition'])
                else:
                    error = _("le livre n'est pas ouvert aux propositions PRIX.")
            if not error:
                if form.is_valid():
                    obj = form.save(commit=False)
                    if obj.get_type()=='NUMBER':
                        livre = self.get_object()
                        if obj.valeur<livre.get_cout_production()['prix_exemplaire']:
                            response_data = {
                                'errors': {'__all__': [force_text('Le prix ne peut etre inferieur au cout de production')]},
                            }
                            return HttpResponse(json.dumps(response_data), content_type="application/json")
                    obj.auteur = request.user
                    obj.livre=self.get_object()
                    try:
                        obj.type=data['type_proposition']
                    except:
                        pass
                    if self.is_presouscription_transform():
                        #quand la presouscription se transforme en souscription, les propositions de l'auteurs sont automatiquement choisies
                        obj.private=True
                        obj.save()
                        obj.choisir()
                    else:
                        obj.save()
                presouscription_transform = (self.object.phase == 'CREA-FEE') and (self.request.user in self.object.auteurs.all())
                sondages_data = SondageApiSerializer(self.object, context={'request': self.request,'presouscription_transform':presouscription_transform}).data
                response_data = {
                    'sondages' : sondages_data,
                    'errors': form.errors,
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")
            else:
                response_data = {
                    'errors': {'__all__': [force_text(error)]},
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")

        if self.is_editable()['general'] and data.has_key("livre"):
            success_url=""
            form = LivreForm(data=data['livre'],instance=self.get_object())
            if form.is_valid():
                obj = form.save()
                if data['validation']:
                    #une demande de validation a ete faite sur le livre, on va donc faire des tests
                    error=""
                    error_count=0
                    if obj.resume=="":
                        error_count +=1
                        form._errors['resume'] = [force_text(_("Vous n'avez pas rempli de resume"))]
                    if obj.biographie=="":
                        error_count +=1
                        form._errors['biographie'] = [force_text(_("Vous n'avez pas rempli de biographie"))]
                    if obj.titre=="":
                        error_count +=1
                        form._errors['titre'] = [force_text(_("Vous n'avez pas rempli de titre"))]
                    if obj.type_extraits=="NEVER_OPENED":
                        if obj.extrait1_type=="T":
                            if len(obj.extrait1_txt)==0:
                                error_count +=1
                                form._errors['extrait1_txt'] = [force_text(_("Vous n'avez pas rempli l'extrait 1 texte"))]
                        else:
                            if not obj.extrait1_img:
                                error_count +=1
                                form._errors['extrait1_img'] = [force_text(_("Vous n'avez pas rempli l'extrait 1 image"))]
                        if obj.extrait2_type=="T":
                            if len(obj.extrait2_txt)==0:
                                error_count +=1
                                form._errors['extrait2_txt'] = [force_text(_("Vous n'avez pas rempli l'extrait 2 texte"))]
                        else:
                            if not obj.extrait2_img:
                                error_count +=1
                                form._errors['extrait2_img'] = [force_text(_("Vous n'avez pas rempli l'extrait 2 image"))]
                        if obj.extrait3_type=="T":
                            if len(obj.extrait3_txt)==0:
                                error_count +=1
                                form._errors['extrait3_txt'] = [force_text(_("Vous n'avez pas rempli l'extrait 3 texte"))]
                        else:
                            if not obj.extrait3_img:
                                error_count +=1
                                form._errors['extrait3_img'] = [force_text(_("Vous n'avez pas rempli l'extrait 3 image"))]
                        if obj.extrait4_type=="T":
                            if len(obj.extrait4_txt)==0:
                                error_count +=1
                                form._errors['extrait4_txt'] = [force_text(_("Vous n'avez pas rempli l'extrait 4 texte"))]
                        else:
                            if not obj.extrait4_img:
                                error_count +=1
                                form._errors['extrait4_img'] = [force_text(_("Vous n'avez pas rempli l'extrait 4 image"))]
                    else:
                        if len(obj.instructions_extraits)==0:
                            form._errors['instructions_extraits'] = [force_text(_("Vous n'avez pas donne d'instruction concernant le vote sur les extraits"))]
                            error_count +=1
                    if obj.type_extraits=="READ_ONLY":
                        if (TextProposition.objects.filter(livre=obj,type='EXTRA').count() + ImageProposition.objects.filter(livre=obj,type='EXTRA').count())<4:
                            error += force_text(_("Vous avez ouvert aux votes les extraits sans faire au moins quatre propositions"))
                            error_count +=1

                    if obj.type_titres=="READ_ONLY":
                        if CharProposition.objects.filter(livre=obj).count()<2:
                            error += force_text(_("Vous avez ouvert aux votes les titres sans faire au moins deux propositions"))
                            error_count +=1

                    if obj.type_prix=="READ_ONLY":
                        if NumberProposition.objects.filter(livre=obj).count()<2:
                            error += force_text(_("Vous avez ouvert aux votes les prix sans faire au moins deux propositions"))
                            error_count +=1

                    if obj.type_couvertures=="READ_ONLY":
                        if ImageProposition.objects.filter(livre=obj,type='COVER').count()<2:
                            error += force_text(_("Vous avez ouvert aux votes l'image de couverture sans faire au moins deux propositions"))
                            error_count +=1

                    if obj.type_biographies=="NEVER_OPENED":
                        if len(obj.biographie)==0:
                            form._errors['biographie'] = [force_text(_("Vous n'avez pas rempli de biographie"))]
                            error_count +=1
                    else:
                        if len(obj.instructions_biographie)==0:
                            form._errors['instructions_biographie'] = [force_text(_("Vous n'avez pas donne d'instruction concernant le vote sur votre biographie"))]
                            error_count +=1
                    if obj.type_biographies=="READ_ONLY":
                        if TextProposition.objects.filter(livre=obj,type='BIO').count()<2:
                            error += force_text(_("Vous avez ouvert aux votes la biographie sans faire au moins deux propositions"))
                            error_count +=1

                    if obj.pre_souscription:
                        if len(obj.instructions)==0:
                            form.errors['instructions']=[force_text(_("Vous n'avez pas donne d'instructions pour aider vos lecteurs"))]
                            error_count +=1

                        if obj.type_extraits=="NEVER_OPENED" and \
                           obj.type_titres=="NEVER_OPENED" and \
                           obj.type_prix=="NEVER_OPENED" and \
                           obj.type_couvertures=="NEVER_OPENED" and \
                           obj.type_biographies=="NEVER_OPENED":
                            error += force_text(_("Pour la presouscription, vous devez au moins ouvrir une rubrique aux sondages"))
                            error_count +=1

                    if obj.prix_vente==None:
                        error += force_text(_("Votre texte n'a pas de prix, mais votre livre doit en avoir un"))
                        error_count +=1

                    if error_count ==0:
                        if obj.phase =='CREATION':
                            obj.phase='FROZEN'
                        elif obj.phase == 'CREATRAN':
                            obj.phase='FROZ-FEE'
                        obj.save()
                    else:
                        form.errors['__all__'] = [error]
                        response_data = {
                            'errors': form.errors,
                        }
                        return HttpResponse(json.dumps(response_data), content_type="application/json")


                success_url=reverse('livre_detail', args=[obj.slug])
                response_data = {
                    'livre': LivreApiSerializer(self.get_object(), context={'request': self.request}).data,
                    'errors': form.errors,
                    'success_url':success_url if data['validation'] else None
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")

            else:
                response_data = {
                    'errors': form.errors,
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")


        if self.object.phase=='CREA-FEE':
            if data['validation']:
                try:
                    self.object.presouscription_transform()
                    response_data = {
                        'success_url':self.object.url(),
                    }
                    return HttpResponse(json.dumps(response_data), content_type="application/json")
                except Exception as e:
                    error = e.message
                    response_data = {
                        'errors': {'__all__': [force_text(error)]},
                    }
                    return HttpResponse(json.dumps(response_data), content_type="application/json")
            else:
                response_data = {
                    'success_url':None,
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")
        raise Http404


class PanierView(FormView):
    template_name = 'bibliocratie/panier.html'
    form_class = BibliocratieCouponForm
    success_url = reverse_lazy('home')

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        return super(Commande, self).post(request, **kwargs)

    def ajax(self, request):
        form = self.form_class(data=json.loads(request.body))
        panier = Commande.objects.getUserPanier(self.request)
        try:
            if form.is_valid():
                panier.addDiscount(form.discount)
            error = form.errors
        except Exception as inst:
            error = {'__all__': [inst.args[0]]}
        response_data = {
            'panier': PanierApiSerializer(panier).data,
            'errors': error,
            'success_url': force_text(self.success_url)
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json")


class CheckoutView(FormView):
    template_name = 'bibliocratie/checkout.html'
    form_class = AdresseForm

    def get(self, request, *args, **kwargs):
        panier = Commande.objects.getUserPanier(self.request)
        if panier.existe():
            return super(CheckoutView,self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('livre_list'))

    @method_decorator(csrf_protect)
    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        return super(CheckoutView, self).post(request, **kwargs)

    def ajax(self, request):
        data = json.loads(request.body)
        proceed_with_payment = True
        adresse_facturation_form = None
        adresse_livraison_form = None
        checkout_form = None
        panier = Commande.objects.getUserPanier(self.request)
        if data.has_key('checkout_data'):
            checkout_form = CheckoutForm(data=data['checkout_data'])
            if checkout_form.is_valid():
                if checkout_form.cleaned_data['diff_address'] == True:
                    if data.has_key('livraison_data'):
                        adresse_livraison_form = AdresseForm(data=data['livraison_data'],instance=panier.adresse_livr)
                        if adresse_livraison_form.is_valid():
                            panier.livraison_autre_adresse = True
                            adresse_livr = adresse_livraison_form.save()
                        else:
                            proceed_with_payment = False

        if data.has_key('facturation_data'):
            adresse_facturation_form = AdresseForm(data=data['facturation_data'],instance=panier.adresse_fact)
            if adresse_facturation_form.is_valid():
                adresse_fact = adresse_facturation_form.save()
                adresse_user = request.user.adresse
                adresse_user.copy(adresse_fact)
                adresse_user.save()
            else:
                proceed_with_payment = False
        result = None
        if proceed_with_payment and panier.total_sans_discount_ni_taxes!=0:
            payline_wsdl_url = finders.find('payline/payline_v4.38.wsdl')
            client = Client(url='file://' + payline_wsdl_url)
            client.set_options(
                location=settings.PAYLINE_URL,
                username=settings.PAYLINE_MERCHANT_ID,
                password=settings.PAYLINE_ACCESS_KEY)
            payline_xml_url = finders.find('payline/payline_doWebPaymentRequest.xml')
            xml_request = open(payline_xml_url, 'rb').read()
            panier.save()
            xml_request = xml_request \
                .replace('REPLACEME_date', timezone.now().strftime('%d/%m/%Y %H:%M')) \
                .replace('REPLACEME_amount', str(int(100 * panier.prix))) \
                .replace('REPLACEME_command_ref', '%08d' % int(panier.no_commande)) \
                .replace('REPLACEME_contract_number', settings.PAYLINE_CONTRACT_NUMBER) \
                .replace('REPLACEME_server', get_current_site(self.request).domain) \
                .replace('REPLACEME_lastname', panier.client.nom) \
                .replace('REPLACEME_firstname', panier.client.prenom) \
                .replace('REPLACEME_email', panier.client.email) \
                .replace('REPLACEME_customer_id', unicode(panier.client.id))
            result = client.service.doWebPayment(__inject={'msg': xml_request})
            logger.debug("result doWebPayment : " + str(result))
            if result.result.code == '00000':
                panier.payline_token = result.token
                panier.valider()


        response_data = {'errors_livraison': adresse_livraison_form.errors if adresse_livraison_form else None,
                         'errors_facturation': adresse_facturation_form.errors if adresse_facturation_form else None,
                         'errors_checkout': checkout_form.errors if checkout_form else None,
                         'success_url': force_text(result.redirectURL) if result else None
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(CheckoutView, self).get_context_data(**kwargs)
        panier = Commande.objects.getUserPanier(self.request)
        panier.adresse_fact.copy(self.request.user.adresse)
        panier.save()
        context.update(
           adresse_facturation_form=AdresseForm(auto_id=u'id1_%s', form_name='facturation_form',scope_prefix="facturation_data", instance = panier.adresse_fact),
           adresse_livraison_form=AdresseForm(auto_id=u'id2_%s', form_name='livraison_form',scope_prefix="livraison_data",instance = panier.adresse_livr),
           checkout_form=CheckoutForm(data={'diff_address': panier.livraison_autre_adresse}),
        )
        return context


class RetourPaylineView(TemplateView):
    template_name = "bibliocratie/retour_payline.html"

    # def get(self, request, *args, **kwargs):
    #     context = self.get_context_data(**kwargs)
    #     if context['commande'].etat=='REF':
    #         return HttpResponseRedirect(reverse('livre_list'))
    #     return self.render_to_response(context)

    def get_context_data(self, **kwargs):

        context = super(RetourPaylineView, self).get_context_data(**kwargs)

        try:
            payline_token = self.request.GET['token']
        except MultiValueDictKeyError:
            return {'status_retour': "erreur : pas de token payline"}

        try:
            panier = Commande.objects.get(payline_token=payline_token)
        except ObjectDoesNotExist:
            context.update(
                status_retour = "erreur : pas de panier correspondant au token payline",
            )

        panier.UpdatePaylineStatus()

        if panier.etat=='PAY':
            context.update(
                status_retour = "ok",
                commande = panier,
            )

        elif panier.etat=='ARR':
            panier.annuler()
            context.update(
                status_retour = "paiement arrété",
                commande = panier,
            )

        elif panier.etat=='REF':
            panier.refuser()
            context.update(
                status_retour = "paiement refusé",
                commande = panier,
            )

        elif panier.etat=='PEN':
            context.update(
                status_retour = "paiement indécis",
                commande = panier,
            )
        context['user_form'] = BiblioUserBiolieu(instance=self.request.user)
        return context

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        raise Http404

    def ajax(self,request):
        user_form = None
        if request.FILES.has_key('avatar'):
            request.FILES.keys().index('avatar')
            user_form = BiblioUserFileForm(request.POST, request.FILES, instance=self.request.user)
            if user_form.is_valid():
                obj = user_form.save()
            return HttpResponse(json.dumps({}), content_type="application/json")
        else:
            data=json.loads(request.body)
            user = self.request.user

            user_form = BiblioUserBiolieu(data=data,instance=user)
            if user_form.is_valid():
                obj = user_form.save(commit=False)
                obj.need_more_info=False
                obj.save()
        response_data = {
            'errors' : user_form.errors,
            'successurl' : reverse('profil_detail',kwargs={'slug':request.user.slug})
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

class PasswordResetView(TemplateView):
    template_name = "mail/password_reset.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk', None)
        user = BiblioUser.objects.get(pk=pk, is_active=True)
        current_site = get_current_site(self.request)
        site_name = current_site.name
        domain = current_site.domain

        context={
                    'email': user.email,
                    'domain': domain,
                    'site_name': site_name,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'user': user,
                    'protocol': 'http',
                    'token': default_token_generator.make_token(user),
                },
        return context[0]


class NotifPaylineView(View):
    def get(self,request):
        #http://URL_DE_NOTIFICATION?notificationType=webtrs&token=TOKEN_LORS_DU_DOWEBPAYMENT
        notificationType = request.GET.get('notificationType')
        payline_token = request.GET.get('token')
        print "notificationtype" + notificationType
        print "payline token" + payline_token
        if notificationType=='WEBTRS':
            try:
                panier = Commande.objects.get(payline_token=payline_token)
            except ObjectDoesNotExist:
                print "Le payline_token " + unicode(payline_token) + "n'existe pas"
                return HttpResponse('pas ok')

            panier.UpdatePaylineStatus()
            return HttpResponse('ok')
        return HttpResponse('pas ok')


class StaffView(TemplateView):
    template_name = "bibliocratie/staff.html"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(StaffView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        presouscriptions = Livre.objects.filter(phase='FEEDBACK', is_active=True)
        nb_votes = Vote.objects.filter(proposition__livre__phase='FEEDBACK').count()
        nb_propositions = Proposition.objects.filter(livre__phase='FEEDBACK').count()
        nb_commentaires = Commentaire.objects.filter(livre__phase__in=['FEEDBACK','GETMONEY','SUCCES','ECHEC']).count()
        nb_succes = Livre.objects.filter(phase='SUCCES', is_active=True).count()
        nb_echecs = Livre.objects.filter(phase='ECHEC', is_active=True).count()
        nb_finished = nb_succes+nb_echecs
        context={
                    'nb_users': BiblioUser.objects.count(),
                    'nb_commentaires': nb_commentaires,
                    'nb_votes': nb_votes,
                    'nb_propositions':nb_propositions,
                    'nb_souscriptions':Livre.objects.filter(phase='GETMONEY', is_active=True).count(),
                    'nb_presouscriptions': presouscriptions.count(),
                    'nb_crea_souscriptions': Livre.objects.filter(phase='CREATION',pre_souscription=False, is_active=True).count(),
                    'nb_crea_presouscriptions': Livre.objects.filter(phase='CREATION',pre_souscription=True, is_active=True).count(),
                    'nb_frozen_souscriptions': Livre.objects.filter(phase='FROZEN',pre_souscription=False, is_active=True).count(),
                    'nb_frozen_presouscriptions': Livre.objects.filter(phase='FROZEN',pre_souscription=True, is_active=True).count(),
                    'nb_valid_souscriptions': Livre.objects.filter(phase='VALIDATE',pre_souscription=False, is_active=True).count(),
                    'nb_valid_presouscriptions': Livre.objects.filter(phase='VALIDATE',pre_souscription=True, is_active=True).count(),
                    'nb_succes': nb_succes,
                    'nb_echecs': nb_echecs,
                    'pc_success': unicode(Decimal(float(nb_succes)*100/float(nb_finished)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) if nb_finished else None,
                    'pc_echecs': unicode(Decimal(float(nb_echecs)*100/float(nb_finished)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) if nb_finished else None,
                    'user_form' : BiblioUserEmailForm(),
                    'adresse_cli_form' : AdresseForm(auto_id=u'id1_%s', form_name='adresse_cli_form',scope_prefix="adresse_cli_data"),
                    'adresse_fact_form' : AdresseForm(auto_id=u'id2_%s', form_name='facturation_form',scope_prefix="facturation_data"),
                    'adresse_livr_form' : AdresseForm(auto_id=u'id3_%s', form_name='livraison_form',scope_prefix="livraison_data"),
                    'diff_form' : CheckoutForm(),
                },
        return context[0]

    def post(self, request, **kwargs):
        if request.is_ajax():
            return self.ajax(request)
        return super(StaffView, self).post(request, **kwargs)

    def ajax(self, request):
        data = json.loads(request.body)
        if data.has_key('client') and data.has_key('adresse'):
            client_form = BiblioUserEmailForm(data=data['client'])
            adresse_form = AdresseForm(data=data['adresse'])
            if adresse_form.is_valid() and client_form.is_valid():
                adresse = adresse_form.save()
                client = client_form.save(commit=False)
                client.adresse = adresse
                client.save()
            response_data = {
                'client': client_form.errors,
                'adresse': adresse_form.errors
            }
        elif data.has_key('commande') and data.has_key('adresse_fact') and data.has_key('adresse_livr'):
            dif = False
            if data.has_key('diff'):
                dif = data['diff']['diff_address']
            try:
                client = BiblioUser.objects.get(id=data['commande']['client']['id'], is_active=True)
            except:
                response_data = {
                    'error_msg' : u"Le client n'a pas été reconnu",
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")

            souscriptions = data['commande']['souscriptions']

            if not len(souscriptions):
                response_data = {
                    'error_msg' : u"Votre commande ne contient aucune souscription",
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")

            if not data['commande'].has_key('info'):
                response_data = {
                    'error_msg' : u"Veuillez renseigner le champ commentaire/no cheque",
                }
                return HttpResponse(json.dumps(response_data), content_type="application/json")


            adresse_fact_form = AdresseForm(data=data['adresse_fact'])
            if adresse_fact_form.is_valid():
                ok=True
            else:
                ok=False
            adresse_livr_form = None
            if dif:
                adresse_livr_form = AdresseForm(data=data['adresse_livr'])
                if adresse_livr_form.is_valid():
                    ok=True
                else:
                    ok=False

            if ok:
                commande = Commande(client=client,etat='PAY', infos=data['commande']['info'])
                commande.save()

                adresse_fact=commande.adresse_fact
                adresse_fact.copy(adresse_fact_form.save(commit=False))
                adresse_fact.save()

                adresse_cli=client.adresse
                adresse_cli.copy(adresse_fact)
                adresse_cli.save()

                adresse_livr=commande.adresse_livr
                if dif:
                    adresse_livr.copy(adresse_livr_form.save())
                    adresse_livr.save()
                    commande.livraison_autre_adresse=True
                    commande.save()

                for achat in souscriptions:
                    livre = Livre.objects.get(id=achat['id'], is_active=True)
                    souscription = Souscription(livre=livre, etat='ENC',quantite=achat['quantite'],panier=commande)
                    souscription.save()

            response_data = {
                'facturation': adresse_fact_form.errors,
                'livraison': adresse_livr_form.errors if adresse_livr_form else None,
                'commande' : CommandeSerializer(commande, context={'request': self.request}).data if ok else None,
            }
        return HttpResponse(json.dumps(response_data), content_type="application/json")


class LancementJsonView(JSONResponseMixin, View):

    @allow_remote_invocation
    def GetDatesDebut(self, in_data):
        livre_id = in_data['livre_id']
        livre = Livre.objects.get(id=livre_id, is_active=True)
        TODAY = date.today()
        dates_possibles = []
        if (TODAY.isoweekday() in [1,2,3]):
            date_possible = TODAY+relativedelta(weekday=WE(+2))
        else:
            date_possible = TODAY+relativedelta(weekday=WE(+1))
        no_semaine = 1
        MAX_SEMAINES = 8
        while no_semaine<=MAX_SEMAINES :
            dates_possibles.append({'title':str(no_semaine),'start':date_possible,'id':str(no_semaine),
                                       'tooltip':"Choix possible",
                                       'tooltipPlacement':"left",
                                       'tooltipNotSelected':"Choix possible",
                                       'titre':"Pre-souscript." if livre.pre_souscription else "Souscription",
                                       'tooltipSelected':"Debut de la pre-souscription" if livre.pre_souscription else "Debut de la souscription"})
            date_possible = date_possible + relativedelta(weeks=+1)
            no_semaine += 1

        event_souscription=None
        if livre.pre_souscription:
            paris = pytz.timezone('Europe/Paris')
            event_souscription =  {'title':"Souscription",
                                   'start':livre.date_souscription.astimezone(paris).date().isoformat() if livre.date_souscription else None,
                                   'id':"1",
                                   'tooltip':"Date de souscription",
                                   'tooltipPlacement':"left",
                                   'tooltipNotSelected':"Choix possible",
                                   'tooltipSelected':"Debut de la souscription",
                                   'titre':"Souscription",
                                   }

        return {'dates_possibles' : dates_possibles,
                'pre_souscription' : livre.pre_souscription,
                'event_souscription': event_souscription}

    @allow_remote_invocation
    def GetDatesFin(self, in_data):
        date_debut = in_data['date_debut']
        livre_id = in_data['livre_id']
        livre = Livre.objects.get(id=livre_id, is_active=True)
        date_debut = dateutil.parser.parse(date_debut)
        dates_fin_souscription = []
        if livre.pre_souscription:
            date_possible = date_debut+relativedelta(weekday=SA(+1),weeks=+3)
            date_souscription = date_debut + relativedelta(weekday=WE(+3))
        else:
            date_possible = date_debut+relativedelta(weekday=SA(+1),weeks=+1)
            date_souscription = date_debut

        if livre.nb_jours_campagne:
            date_fin = date_souscription + relativedelta(days=livre.nb_jours_campagne)
        else:
            date_fin=None
        no_semaine = 1
        MAX_SEMAINES = 8
        while no_semaine<=MAX_SEMAINES :
            dates_fin_souscription.append({'title': "Fin de souscription" if date_fin==date_possible else str(no_semaine),
                                           'start':date_possible.date().isoformat(),
                                           'id':str(no_semaine),
                                           'className' : ['date-choisie'] if date_fin==date_possible else [],
                                           'tooltip':"Fin de souscription" if date_fin==date_possible else "Choix possible",
                                           'tooltipPlacement':"left",
                                           'tooltipNotSelected':"Choix possible",
                                           'titre':"Fin souscript.",
                                           'tooltipSelected':"Fin de la souscription"})
            date_possible = date_possible + relativedelta(weeks=+1)
            no_semaine += 1


        return {'dates_fin_souscription' : dates_fin_souscription,
                'date_souscription': {'titre':'Souscription',
                                      'start':date_souscription.date().isoformat(),'id':str(no_semaine),
                                      'tooltip':"Souscription",
                                      'tooltipPlacement':"left",
                                      'tooltipNotSelected':"Choix possible",
                                      'tooltipSelected':"Début de la souscription"
                                      },
                'pre_souscription' : livre.pre_souscription, #true or false
                'date_fin':date_fin.date().isoformat() if date_fin else None,
        }

    @allow_remote_invocation
    def GetCoutProduction(self, in_data):
        if in_data.has_key('livre_id') and in_data.has_key('nb_exemplaires_cible'):
            livre=Livre.objects.get(id=in_data['livre_id'], is_active=True)
            livre.nb_exemplaires_cible=in_data['nb_exemplaires_cible']
            return livre.get_cout_production()
        else:
            return {
                'message' : None,
                'prix_exemplaire' : None,
            }


    @allow_remote_invocation
    def RefreshData(self, in_data):
        livre_id=in_data['livre_id']
        livre = Livre.objects.get(pk=livre_id, is_active=True)
        out_data = {
            'url_fichier': livre.fichier_auteur.url if hasattr(livre.fichier_auteur, 'url') else "",
            'nom_fichier': livre.fichier_auteur.name,
            'image_couverture': livre.image_300x400_url(),
            'maquette_couverture': livre.maquete_couverture.url if hasattr(livre.maquete_couverture, 'url') else "",
            'maquette_couverture_fichier_name': livre.maquete_couverture.name,
            'success': True,
        }
        return out_data


class GlobalSearchJsonView(JSONResponseMixin, View):

    @allow_remote_invocation
    def Search(self, in_data):
        search_results = watson.search(in_data['search'])
        meta_list=[]
        for result in search_results:
            if result.meta:
                 meta_list.append(result.meta)
        return {'list':meta_list,'search':in_data['search']}


class PanierJsonView(JSONResponseMixin, View):
    '''
    est connecté au Controlleur PanierCtrl
    '''

    @allow_remote_invocation
    def addLivre(self, in_data):
        """
        si in_data['livre_id']==-1 renvoie sumplement le panier
        """
        livre_id = in_data['livre_id']
        panier = Commande.objects.getUserPanier(self.request)
        message = ""

        # Si livre_id = -1, il s'agit juste d'un refresh du panier
        if livre_id != -1:
            livre= Livre.objects.get(id=livre_id, is_active=True)
            #si le livre n'est pas en souscription, pas d'achat possible
            if livre.phase == 'GETMONEY':
                panier.save()
                quantite = in_data['quantite']
                panier.addSouscription(in_data['livre_id'],quantite)
            else:
                message = _("Ajout au panier impossible : le livre n'est pas en souscription")


        out_data = {
            'panier': PanierApiSerializer(panier, context={'request': self.request}).data,
            'success': True,
            'message': force_text(message),
        }
        return out_data

    @allow_remote_invocation
    def removeLivre(self, in_data):
        """
        si in_data['livre_id']==-1 renvoie sumplement le panier
        """
        livre_id = in_data['livre_id']
        panier = Commande.objects.getUserPanier(self.request)

        panier.removeLivre(in_data['livre_id'])

        out_data = {
            'panier': PanierApiSerializer(panier,context={'request': self.request}).data,
            'success': True,
        }
        return out_data

    @allow_remote_invocation
    def removeSouscriptions(self, in_data):
        """
        Retrait de toutes les occurences d'un livre dans un panier
        """
        souscription_id = in_data['souscription_id']
        panier = Commande.objects.getUserPanier(self.request)
        for souscription in panier.souscription_set.all():
            if souscription.id == souscription_id:
                souscription.delete()
        out_data = {
            'panier': PanierApiSerializer(panier, context={'request': self.request}).data,
            'success': True,
        }
        return out_data

    @allow_remote_invocation
    def removeDiscount(self, in_data):
        """
        Retrait de toutes les occurences d'une discount dans un panier
        """
        discount_id = in_data['discount_id']
        discount = Discount.objects.get(id=discount_id)
        discount.delete()
        panier = Commande.objects.getUserPanier(self.request)
        out_data = {
            'panier': PanierApiSerializer(panier, context={'request': self.request}).data,
            'success': True,
        }
        return out_data

    @allow_remote_invocation
    def setPaysLivraison(self, in_data):
        """
        Indique au panier le pays de livraison, pour recalculer les frais de port
        """
        pays = in_data
        panier = Commande.objects.getUserPanier(self.request)
        panier.setPaysLivraison(pays)
        out_data = {
            'panier': PanierApiSerializer(panier, context={'request': self.request}).data,
            'success': True,
        }
        return out_data

    @allow_remote_invocation
    def goToOrder(self, in_data):
        """
        Vérifie si l'utilisateur est authentifié et renvoie l'adresse du checkout
        """
        if self.request.user.is_authenticated():
            out_data = {
                'success_url': reverse('checkout'),
                'is_authenticated': True,
                'success': True,
            }
        else:
            out_data = {
                'success_url': reverse('checkout'),
                'is_authenticated': False,
                'success': True,
            }
        return out_data

    @allow_remote_invocation
    def lancerMonProjet(self, in_data):
        """
        Vérifie si l'utilisateur est authentifié et renvoie l'adresse du checkout
        """
        if self.request.user.is_authenticated():
            out_data = {
                'success_url': reverse('lancement'),
                'is_authenticated': True,
                'success': True,
            }
        else:
            out_data = {
                'success_url': reverse('lancement'),
                'is_authenticated': False,
                'success': True,
            }
        return out_data


class ProfilJsonView(JSONResponseMixin, View):
    '''

    '''

    @allow_remote_invocation
    def follow(self, in_data):
        user = self.request.user
        if not user.is_authenticated():
            if not in_data.has_key('question'):
                out_data = {
                    'success': False,
                    'message': unicode(_("Vous devez etre authentifie pour suivre quelqu'un")),
                }
            else:
                out_data = {
                    'css_follow': "non",
                    'txt_follow': "Suivre",
                    'success': True,
                }

        else:
            followee=BiblioUser.objects.get(pk=in_data['userid'], is_active=True)
            if user!=followee:
                f=Follow.objects.filter(qui=user,suit=followee).first()
                if f:
                    css_follow=f.lien.lower()
                else:
                    css_follow="non"
                if not in_data.has_key('question'):
                    f,created=Follow.objects.get_or_create(qui=user,suit=followee)
                    if created or f.lien=="ENN":
                        f.lien = 'AMI'
                    else:
                        f.lien = 'ENN'
                    f.save()
                    css_follow = f.lien.lower()
                if css_follow=="non":
                    txt_follow = "Suivre"
                if css_follow=="ami":
                    txt_follow = "Ne plus suivre"
                if css_follow=="enn":
                    txt_follow = "Suivre"
            else:
                css_follow = force_text(_("non"))
                txt_follow = force_text(_("Vous ne pouvez pas vous follower vous meme"))
            out_data = {
                'css_follow': css_follow,
                'txt_follow': txt_follow,
                'success': True,
            }
        return out_data

    @allow_remote_invocation
    def comment(self, in_data):
        user = self.request.user
        if user.is_authenticated():
            if in_data.has_key('commentaire'):
                timeline = Timeline.objects.get(id=in_data['timelineid'])
                commentaire = TimelineCommentaire(user=user,contenu=in_data['commentaire'][:400],timeline=timeline)
                commentaire.save()
                timeline.timestamp=timezone.now()
                timeline.save()
                out_data = {
                    'timeline': TimelineApiSerializer(timeline, context={'request': self.request}).data,
                    'success': True,
                }
            else:
                out_data = {
                    'timeline': False,
                    'success': unicode(_("Votre commentaire est vide")),
                }
        else:
            out_data = {
                'success': False,
                'message': unicode(_("Vous devez etre authentifie pour comenter")),
            }
        return out_data

    @allow_remote_invocation
    def getCommandes(self, in_data):
        user = self.request.user
        if user.is_authenticated():
            commandes = Commande.objects.filter(client=user,etat='PAY')
            out_data = {
                'commandes': CommandeSerializer(commandes, context={'request': self.request}, many=True).data,
                'success': True,
            }
        else:
            out_data = {
                'success': False,
                'message': unicode(_("Vous devez etre authentifie pour lister vos commandes")),
            }
        return out_data

    @allow_remote_invocation
    def passRecover(self, in_data):
        user = self.request.user
        if user.is_authenticated():
            current_site = get_current_site(self)
            site_name = current_site.name
            domain = current_site.domain

            subject = _("Reinitialisation de votre mot de passe")
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
            out_data = {
                'success': True,
                'message': unicode(_("Un message expliquant la procedure pour changer de mot de passe vient de vous etre envoye"))
            }
        else:
            out_data = {
                'success': False,
                'message': unicode(_("Vous devez etre authentifie pour réinitialiser votre mot de passe")),
            }
        return out_data


class LivreJsonView(JSONResponseMixin, View):
    '''
    est connecté au Controlleur LivreCtrl
    '''

    @allow_remote_invocation
    def getLivre(self, in_data):
        """
        renvoie les infos liées au livre
        """
        livre_id = in_data['livre_id']
        livre = Livre.objects.get(id=livre_id, is_active=True)
        if self.request.user in livre.auteurs.all():
            je_suis_lauteur=True
        else:
            je_suis_lauteur=False
        out_data = {
            'livre': LivreApiSerializer(livre, context={'request': self.request}).data,
            'success': True,
            'je_suis_lauteur': je_suis_lauteur,
        }
        return out_data

    @allow_remote_invocation
    def getSelecteurs(self):
        """
        renvoie les categories disponibles
        """
        categories= Livre.objects.filter(is_active=True,phase='GETMONEY').annotate(nb_souscription=Count('souscription')).filter(nb_souscription__gt=4).values('category').annotate(count=Count('category'))
        genres = Livre.objects.filter(is_active=True,phase='GETMONEY').annotate(nb_souscription=Count('souscription')).filter(nb_souscription__gt=4).values('genre').annotate(count=Count('genre'))
        etats = Livre.objects.filter(is_active=True,phase='GETMONEY').annotate(nb_souscription=Count('souscription')).filter(nb_souscription__gt=4).values('etat').annotate(count=Count('etat'))
        phases = ['GETMONEY','SUCCES','ECHEC']

        for categorie in categories:
            categorie['display']=force_text(dict(Livre.TYPE_CATEGORY).get(categorie['category'], categorie['category']), strings_only=True)

        for genre in genres:
            genre['display']=force_text(dict(Livre.TYPE_GENRE).get(genre['genre'], genre['genre']), strings_only=True)

        for etat in etats:
            etat['display']=force_text(dict(Livre.TYPE_ETAT).get(etat['etat'], etat['etat']), strings_only=True)


        categories_json=[{'key':"",'value':force_text(dict(Livre.TYPE_CATEGORY).get('', ''), strings_only=True)}]
        for categorie in categories:
            categories_json.append({'key':categorie['category'],'value':force_text(dict(Livre.TYPE_CATEGORY).get(categorie['category'], categorie['category']), strings_only=True)})

        genres_json=[{'key':"",'value':force_text(dict(Livre.TYPE_GENRE).get('', ''), strings_only=True)}]
        for genre in genres:
            genres_json.append({'key':genre['genre'],'value':force_text(dict(Livre.TYPE_GENRE).get(genre['genre'], genre['genre']), strings_only=True)})

        etat_nul_trouve = False
        for etat in etats:
            if etat['etat']=="":
                etat_nul_trouve=True
                break
        if not etat_nul_trouve:
            etats_json=[{'key':"",'value':force_text(dict(Livre.TYPE_ETAT).get('', ''), strings_only=True)}]
        else:
            etats_json = []
        for etat in etats:
            etats_json.append({'key':etat['etat'],'value':force_text(dict(Livre.TYPE_ETAT).get(etat['etat'], etat['etat']), strings_only=True)})

        phases_json=[]
        for phase in phases:
            phases_json.append({'key':phase,'value':force_text(dict(Livre.PHASES).get(phase, phase), strings_only=True)})

        out_data = {
            'categories': categories_json,
            'genres': genres_json,
            'etats': etats_json,
            'phases': phases_json,
            'success': True,
        }
        return out_data

    @allow_remote_invocation
    def getsondages(self, in_data):
        """
        renvoie les sondages liées au livre
        """
        livre_id = in_data['livre_id']
        try:
            livre=Livre.objects.get(id=livre_id, is_active=True)
            presouscription_transform = (livre.phase == 'CREA-FEE') and (self.request.user in livre.auteurs.all())
            sondages_data = SondageApiSerializer(livre, context={'request': self.request,'presouscription_transform':presouscription_transform}).data
        except:
            sondages_data=None
        out_data = {
            'sondages': sondages_data,
            'success': True,
        }
        return out_data

    @allow_remote_invocation
    def me_rappeler(self, in_data):
        """
        Permet a un user de s'inscrire pour etre rappele peu avant la fin de la souscription.
        """
        user = self.request.user
        livre_api = None
        if user.is_anonymous():
            result=False;
            message=_('Vous devez etre authentifie pour utiliser la fonction de rappel')
        else:
            try:
                livre_id = in_data['livre_id']
                user = self.request.user
                livre=Livre.objects.get(id=livre_id, is_active=True)
                if livre.phase=='GETMONEY':
                    user_rappel,created = MeRappeler.objects.get_or_create(livre=livre,user=user)
                    result = True;
                    if created:
                        message = _('Votre demande a ete enregistree')
                    else:
                        message = _('Votre demande a deja ete enregistree')
                else:
                    result = False;
                    message = _("Cette fonction n'est disponible que pendant la souscription")
            except:
                result = False;
                message = _("Une erreur s'est produite pendant l'enregistrement de votre demande")

        out_data = {
            'success': result,
            'message': force_text(message),
        }
        return out_data

    @allow_remote_invocation
    def demander_new(self, in_data):
        """
        Permet a un user de demander une remise en souscription
        """
        user = self.request.user
        livre_api = None
        if user.is_anonymous():
            result=False;
            message=_('Vous devez etre authentifie pour utiliser la fonction de demande de souscription')
        else:
            try:
                livre_id = in_data['livre_id']
                user = self.request.user
                livre=Livre.objects.get(id=livre_id, is_active=True)
                if livre.phase in ['SUCCES','ECHEC']:
                    user_rappel,created = DemanderNewSouscription.objects.get_or_create(livre=livre,user=user)
                    result = True;
                    if created:
                        message = _('Votre demande a ete enregistree')
                    else:
                        message = _('Votre demande a deja ete enregistree')
                else:
                    result = False;
                    message = _("Cette fonction n'est disponible que pendant la souscription")
            except:
                result = False;
                message = _("Une erreur s'est produite pendant l'enregistrement de votre demande")

        out_data = {
            'livre': LivreApiSerializer(livre, context={'request': self.request}).data if result else None,
            'success': result,
            'message': force_text(message),
        }
        return out_data

    @allow_remote_invocation
    def rate(self, in_data):
        """
        Permet a un user de donner une note à un livre.
        """
        user = self.request.user
        livre_api = None
        if user.is_anonymous():
            result=False;
            message=_('Vous devez etre authentifie pour voter sur un livre')
        else:
            try:
                livre_id = in_data['livre_id']
                user = self.request.user
                livre=Livre.objects.get(id=livre_id, is_active=True)
                if livre.phase=='GETMONEY':
                    user_rate,created = Rating.objects.get_or_create(livre=livre,user=user)
                    user_rate.rating=in_data['rate']
                    user_rate.save()
                    result = True;
                    message = ""
                    livre_api = LivreApiSerializer(livre, context={'request': self.request}).data
                else:
                    result = False;
                    message = _("Le vote n'est ouvert que pendant la souscription")
            except:
                result = False;
                message = _("Une erreur s'est produite pendant l'enregistrement de votre vote")

        out_data = {
            'success': result,
            'message': force_text(message),
            'livre': livre_api
        }
        return out_data

    @allow_remote_invocation
    def vote(self, in_data):
        """
        renvoie les sondages liées au livre
        """
        if not self.request.user.is_authenticated():
            out_data = {
                'success': False,
                'message': force_text(_("Vous devez etre authentifie pour voter")),
            }
            return out_data

        proposition_id = in_data['proposition_id']
        proposition = Proposition.objects.get(pk=proposition_id)

        livre = proposition.getTypedProposition().livre

        if livre.phase=="CREA-FEE" and self.request.user in livre.auteurs.all():
            typedProposition=proposition.getTypedProposition()
            message=""
            try:
                typedProposition.choisir()
                success = True
            except Exception as e:
                success = False
                message = e.message
            presouscription_transform = (livre.phase == 'CREA-FEE') and (self.request.user in livre.auteurs.all())
            out_data = {
                'success': success,
                'message': message,
                'sondages': SondageApiSerializer(livre, context={'request': self.request,'presouscription_transform':presouscription_transform}).data,
            }
            return out_data

        if livre.phase!='FEEDBACK':
            out_data = {
                'success': False,
                'message': force_text(_("Le vote n'est autorise qu'en presouscription")),
            }
            return out_data
        try:
            Vote.objects.get(proposition=proposition,user=self.request.user)

        except Vote.DoesNotExist:
            vote=Vote(proposition=proposition,user=self.request.user)
            vote.save()
        presouscription_transform = (livre.phase == 'CREA-FEE') and (self.request.user in livre.auteurs.all())
        out_data = {
            'livre': LivreApiSerializer(livre, context={'request': self.request}).data,
            'success': True,
            'sondages': SondageApiSerializer(livre, context={'request': self.request,'presouscription_transform':presouscription_transform}).data,
        }
        return out_data

    @allow_remote_invocation
    def remove_proposition(self, in_data):
        """
        renvoie les sondages liées au livre
        """
        proposition_id = in_data['proposition_id']
        proposition = Proposition.objects.get(pk=proposition_id)
        livre = Livre.objects.get(id=proposition.getTypedProposition().livre_id, is_active=True)

        proposition.delete()
        presouscription_transform = (livre.phase == 'CREA-FEE') and (self.request.user in livre.auteurs.all())
        out_data = {
            'success': True,
            'sondages': SondageApiSerializer(livre, context={'request': self.request,'presouscription_transform':presouscription_transform}).data,
        }
        return out_data

    @allow_remote_invocation
    def follow_auteur(self, in_data):
        user = self.request.user
        if not user.is_authenticated():
            out_data = {
                'success': False,
                'message': unicode(_("Vous devez etre authentifie pour suivre quelqu'un")),
            }
        else:
            print in_data['auteur'][0]
            print in_data['auteur'][0]
            livre = Livre.objects.filter(auteurs__id=in_data['auteur'][0], is_active=True).first()
            for auteur in livre.auteurs.all():
                if user!=auteur:
                    f=Follow.objects.filter(qui=user,suit=auteur).first()
                    if f:
                        css_follow=f.lien.lower()
                    else:
                        css_follow="non"
                    if not in_data.has_key('question'):
                        f,created=Follow.objects.get_or_create(qui=user,suit=auteur)
                        if created or f.lien=="ENN":
                            f.lien='AMI'
                        else:
                            f.lien='ENN'
                        f.save()
                        css_follow=f.lien.lower()
                    if css_follow=="non":
                        txt_follow="Suivre"
                    if css_follow=="ami":
                        txt_follow="Ne plus suivre"
                    if css_follow=="enn":
                        txt_follow="Suivre"
                else:
                    css_follow = force_text(_("non"))
                    txt_follow = force_text(_("Vous ne pouvez pas vous follower vous meme"))
                out_data = {
                    'css_follow': css_follow,
                    'txt_follow': txt_follow,
                    'success': True,
                }
        return out_data

class StaffJsonView(JSONResponseMixin, View):
    '''
    est connecté au Controlleur LivreCtrl
    '''

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(StaffJsonView, self).dispatch(*args, **kwargs)

    @allow_remote_invocation
    def getStatVentesJour(self, in_data):
        """
        renvoie les statistiques de vente
        """
        try:
            date_jour = in_data['date_jour']
            dt = dateutil.parser.parse(date_jour)
        except:
            out_data = {
                'success': False
            }
            return out_data
        localtime = dt.astimezone (pytz.timezone('Europe/Paris'))
        debut = datetime(localtime.year, localtime.month, localtime.day)

        commandes=[]
        ventes=[]
        ca = 0
        nb_commandes = 0
        nb_souscriptions = 0
        for heure in range(0,24) :
            time_debut = debut + timedelta(hours=heure)
            timestamp = calendar.timegm(time_debut.timetuple()) * 1000
            time_fin = time_debut + timedelta(hours=1)
            # ch_list = CommandeHistory.objects.filter(etat='PAY',date__gte=time_debut, date__lt=time_fin)
            c_list = Commande.objects.filter(etat='PAY',date__gte=time_debut,date__lt=time_fin).distinct()
            total_euros = 0
            total_commandes = 0
            total_souscriptions = 0
            for commande in c_list:
                total_euros += commande.montant
                for souscription in commande.souscription_set.all():
                    total_souscriptions += souscription.quantite
                total_commandes += 1
            ca += total_euros
            nb_souscriptions += total_souscriptions
            nb_commandes += total_commandes
            commandes.append([timestamp,total_commandes])
            ventes.append([timestamp,total_euros])

        serie_list = [
            {
                'label': "commandes",
                'data': commandes,
                'yaxis': 1
            },
            {
                'label': "€",
                'data': ventes,
                'yaxis': 2
            }
        ]

        options = {
            "series": {
                "lines": {
                    "show": True,
                    "fill": True
                },
                "points": { "show": True }
            },
            'axisLabels': {
                'show': True
            },
            "xaxis": {
                "mode": "time",
                "timeformat": "%Hh"
            },
            "yaxes": [
                {
                    'axisLabel': 'commandes',
                    "tickColor":["#fff"],
                    "tickDecimals": 0,
                    "min":0
                },
                {
                    'axisLabel': "CA",
                    "position": "right",
                    "tickDecimals": 0,
                    "min":0
                }
            ],
            "grid": {
              "hoverable": True,
              "borderWidth": 1,
              "markings": [ { "yaxis": { "from": 0, "to": 300 }, "color": "#fff" }]
            },
            "colors": ["rgb(138,75,117)", "rgb(71,160,62)"],
            "tooltip":True,
            "tooltipOpts": {
                "content": "%x : %y %s"
            },
            "legend": {
                "show": True,
                "labelFormatter": None, # null or (fn: string, series object -> string)
                #"labelBoxBorderColor": color,
                #noColumns: number
                #'position': "ne" or "nw" or "se" or "sw"
                #margin: number of pixels or [x margin, y margin]
                #backgroundColor: null or color
                #backgroundOpacity: number between 0 and 1
                #container: null or jQuery object/DOM element/jQuery expression
                #sorted: null/false, true, "ascending", "descending", "reverse", or a comparator
            }
        };


        out_data = {
            'success': True,
            'souscriptions': serie_list,
            'options': options,
            'ca':ca,
            'nb_commandes':nb_commandes,
            'nb_souscriptions':nb_souscriptions
        }
        return out_data

    @allow_remote_invocation
    def getStatVentesMois(self, in_data):
        """
        renvoie les statistiques de vente
        """

        try:
            date_debut = in_data['date_debut']
            dt_debut = dateutil.parser.parse(date_debut)
            date_fin = in_data['date_fin']
            dt_fin = dateutil.parser.parse(date_fin)
        except:
            out_data = {
                'success': False
            }
            return out_data

        local_dt_debut = dt_debut.astimezone (pytz.timezone('Europe/Paris'))
        debut = datetime(local_dt_debut.year, local_dt_debut.month, local_dt_debut.day)
        local_dt_fin = dt_fin.astimezone (pytz.timezone('Europe/Paris'))
        fin = datetime(local_dt_fin.year, local_dt_fin.month, local_dt_fin.day) + timedelta(days=1)

        commandes=[]
        ventes=[]
        day = 0
        stop = False
        ca = 0
        nb_commandes = 0
        nb_souscriptions = 0
        while not stop :
            time_debut = debut + timedelta(days=day)
            timestamp = calendar.timegm(time_debut.timetuple()) * 1000
            time_fin = time_debut + timedelta(days=1)
            c_list = Commande.objects.filter(etat='PAY',date__gte=time_debut,date__lt=time_fin).distinct()
            # ch_list = CommandeHistory.objects.filter(etat='PAY',date__gte=time_debut, date__lt=time_fin)
            total_euros = 0
            total_souscriptions = 0
            total_commandes = 0

            for commande in c_list:
                total_euros += commande.montant
                for souscription in commande.souscription_set.all():
                    total_souscriptions += souscription.quantite
                total_commandes += 1

            ca+=total_euros
            nb_souscriptions+=total_souscriptions
            nb_commandes+=total_commandes
            commandes.append([timestamp,total_commandes])
            ventes.append([timestamp,total_euros])
            day += 1
            if (debut + timedelta(days=day))>=fin:
                stop=True

        serie_list = [
            {
                'label': "commandes",
                'data': commandes,
                'yaxis': 1
            },
            {
                'label': "€",
                'data': ventes,
                'yaxis': 2
            }
        ]

        options = {
            "series": {
                "lines": {
                    "show": True,
                    "fill": True
                },
                "points": { "show": True }
            },
            'axisLabels': {
                'show': True
            },
            "xaxis": {
                "mode": "time",
                "timeformat": "%e %b",
                "monthNames": ["jan", "fev", "mar", "avr", "mai", "juin", "juil", "aout", "sept", "oct", "nov", "dec"]
            },
            "yaxes": [
                {
                    'axisLabel': 'commandes',
                    "tickColor":["#fff"],
                    "tickDecimals": 0,
                    "min":0
                },
                {
                    'axisLabel': "CA",
                    "position": "right",
                    "tickColor":["#fff"],
                    "tickDecimals": 0,
                    "min":0
                }
            ],
            "grid": {
              "hoverable": True,
              "borderWidth": 1
            },
            "colors": ["rgb(138,75,117)", "rgb(71,160,62)"],
            "tooltip":True,
            "tooltipOpts": {
                "content": "%x : %y %s"
            },
            "legend": {
                "show": True,
                "labelFormatter": None, # null or (fn: string, series object -> string)
                #"labelBoxBorderColor": color,
                #noColumns: number
                #'position': "ne" or "nw" or "se" or "sw"
                #margin: number of pixels or [x margin, y margin]
                #backgroundColor: null or color
                #backgroundOpacity: number between 0 and 1
                #container: null or jQuery object/DOM element/jQuery expression
                #sorted: null/false, true, "ascending", "descending", "reverse", or a comparator
            }
        };


        out_data = {
            'success': True,
            'souscriptions': serie_list,
            'options': options,
            'ca':ca,
            'nb_commandes':nb_commandes,
            'nb_souscriptions':nb_souscriptions
        }
        return out_data

    @allow_remote_invocation
    def getStatVentesAnnee(self, in_data):
        """
        renvoie les statistiques de vente
        """

        try:
            date_debut = in_data['date_debut']
            dt_debut = dateutil.parser.parse(date_debut)
            date_fin = in_data['date_fin']
            dt_fin = dateutil.parser.parse(date_fin)
        except:
            out_data = {
                'success': False
            }
            return out_data

        local_dt_debut = dt_debut.astimezone (pytz.timezone('Europe/Paris'))
        debut = datetime(local_dt_debut.year, local_dt_debut.month,1)
        local_dt_fin = dt_fin.astimezone (pytz.timezone('Europe/Paris'))
        fin = datetime(local_dt_fin.year, local_dt_fin.month,1) + relativedelta(months=+1)

        commandes=[]
        ventes=[]
        month = 0
        stop = False
        ca = 0
        nb_commandes = 0
        nb_souscriptions = 0
        while not stop :
            time_debut = debut + relativedelta(months=+month)
            timestamp = calendar.timegm(time_debut.timetuple()) * 1000
            time_fin = time_debut + relativedelta(months=+1)
            # ch_list = CommandeHistory.objects.filter(etat='PAY',date__gte=time_debut, date__lt=time_fin)
            c_list = Commande.objects.filter(etat='PAY',date__gte=time_debut,date__lt=time_fin).distinct()
            total_euros = 0
            total_souscriptions = 0
            total_commandes = 0
            for commande in c_list:
                total_euros += commande.montant
                for souscription in commande.souscription_set.all():
                    total_souscriptions += souscription.quantite
                total_commandes += 1

            ca+=total_euros
            nb_souscriptions+=total_souscriptions
            nb_commandes+=total_commandes
            commandes.append([timestamp,total_commandes])
            ventes.append([timestamp,total_euros])
            month += 1
            if (debut + relativedelta(months=+month))>=fin:
                stop=True

        serie_list = [
            {
                'label': "commandes",
                'data': commandes,
                'yaxis': 1
            },
            {
                'label': "€",
                'data': ventes,
                'yaxis': 2
            }
        ]

        options = {
            "series": {
                "lines": {
                    "show": True,
                    "fill": True
                },
                "points": { "show": True }
            },
            'axisLabels': {
                'show': True
            },
            "xaxis": {
                "mode": "time",
                "timeformat": "%b %y",
                "monthNames": ["jan", "fev", "mar", "avr", "mai", "juin", "juil", "aout", "sept", "oct", "nov", "dec"]
            },
            "yaxes": [
                {
                    'axisLabel': 'commandes',
                    "tickColor":["#fff"],
                    "tickDecimals": 0,
                    "min":0
                },
                {
                    'axisLabel': "CA",
                    "position": "right",
                    "tickDecimals": 0,
                    "min":0
                }
            ],
            "grid": {
              "hoverable": True,
              "borderWidth": 1
            },
            "colors": ["rgb(138,75,117)", "rgb(71,160,62)"],
            "tooltip":True,
            "tooltipOpts": {
                "content": "%x : %y %s"
            },
            "legend": {
                "show": True,
                "labelFormatter": None, # null or (fn: string, series object -> string)
                #"labelBoxBorderColor": color,
                #noColumns: number
                #'position': "ne" or "nw" or "se" or "sw"
                #margin: number of pixels or [x margin, y margin]
                #backgroundColor: null or color
                #backgroundOpacity: number between 0 and 1
                #container: null or jQuery object/DOM element/jQuery expression
                #sorted: null/false, true, "ascending", "descending", "reverse", or a comparator
            }
        };


        out_data = {
            'success': True,
            'souscriptions': serie_list,
            'options': options,
            'ca':ca,
            'nb_commandes':nb_commandes,
            'nb_souscriptions':nb_souscriptions
        }
        return out_data

class LivreFilter(django_filters.FilterSet):
    class Meta:
        model = Livre
        fields = ['category', 'genre', 'etat','phase','a_la_une',\
                  'type_titres','type_prix','type_couvertures',\
                  'type_extraits','type_biographies','titre']

class SouscriptionFilter(django_filters.FilterSet):
    class Meta:
        model = Livre
        fields = ['category','a_la_une','genre','etat','phase']

class SouscriptionViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = SouscriptionApiSerializer
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    filter_backends = (filters.DjangoFilterBackend,filters.SearchFilter,)
    filter_class = SouscriptionFilter
    search_fields = ('titre',)

    def get_queryset(self):
        return Livre.objects.filter(is_active=True,phase='GETMONEY').annotate(nb_souscription=Count('souscription')).filter(nb_souscription__gt=4,souscription__etat='ENC').order_by('-date_souscription')

class LivreViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Livre.objects.filter(is_active=True)
    serializer_class = LivreApiSerializer
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    filter_backends = (filters.DjangoFilterBackend,filters.SearchFilter,)
    filter_class = LivreFilter
    search_fields = ('titre',)

class CommandeViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Commande.objects.all().order_by('-date')
    serializer_class = PanierApiSerializer
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    filter_backends = (filters.DjangoFilterBackend,)

class TagsViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = (filters.DjangoFilterBackend,)

class TimelineViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = TimelineApiSerializer
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    model = Timeline

    def get_queryset(self):
        try:
            if self.request.QUERY_PARAMS.has_key('user_id'):
                user_id = self.request.QUERY_PARAMS['user_id']
                user = BiblioUser.objects.get(id=user_id, is_active=True)
                if user.is_active:
                    if self.request.user == user:
                        return Timeline.objects.filter(Q(user__id=user_id)| Q(partage__id=user_id)).order_by('-timestamp').distinct()
                    else:
                        return Timeline.objects.filter(Q(user__id=user_id)| Q(partage__id=user_id),private=False).order_by('-timestamp').distinct()
                else:
                    return []
            return Timeline.objects.all()
        except:
            return []


class BiblioUserViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = BiblioUserSerializer
    queryset = BiblioUser.objects.filter(is_active=True)
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = BiblioUser
        fields = ['email','username']

class BiblioStaffUserViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = BiblioStaffUserSerializer
    queryset = BiblioUser.objects.all()
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    filter_backends = (filters.SearchFilter,)
    search_fields = ('email',)

class CommandeStaffViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Commande.objects.all().order_by("-no_commande")
    serializer_class = CommandeSerializer
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    filter_backends = (filters.SearchFilter,)
    search_fields = ('etat','no_commande','pays_livraison','client__adresses__nom','client__adresses__prenom')

class CommentaireStaffViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Commentaire.objects.all().order_by("-id")
    serializer_class = CommentaireSerializer
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    filter_backends = (filters.SearchFilter,)
    search_fields = ('id','user','contenu','date','livre','reponses')


class BiblioUserView(NgCRUDView):
    model = BiblioUser
