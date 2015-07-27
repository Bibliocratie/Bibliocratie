from bibliocratie.forms import BibliocratieAuthenticationForm, BibliocratieSignupForm, BibliocratieRecoverForm, \
    BiblioUserPrefForm, AdresseForm
from bibliocratie.models import Commande
from bibliocratie.forms import ContactForm
from django.conf import settings

def login(request):
    context = dict()
    if not request.user.is_authenticated():
        context['login_form'] = BibliocratieAuthenticationForm()
        context['signup_form'] = BibliocratieSignupForm()
        context['recover_form'] = BibliocratieRecoverForm()
        context['user_form'] = BiblioUserPrefForm()
        context['adresse_form'] = AdresseForm()
    return context

def panier(request):
    context = dict()
    panier = Commande.objects.getUserPanier(request)
    context['panier'] = panier
    return context

def contact_form(request):
    context = dict()
    context['contact_form'] = ContactForm()
    return context

def redactor_upload_dir(request):
    context = dict()
    context['redactor_upload_dir'] = settings.REDACTOR_UPLOAD
    return context

def facebook_app_id(request):
    context = dict()
    context['facebook_app_id'] = settings.FACEBOOK_APP_ID
    return context
