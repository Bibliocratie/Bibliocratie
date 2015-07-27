# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from bibliocratie import views
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse_lazy

from rest_framework import routers
router = routers.SimpleRouter()
router.register(r'livres', views.LivreViewset, base_name='api-livres')
router.register(r'souscriptions', views.SouscriptionViewset, base_name='api-souscriptions')
router.register(r'commandes', views.CommandeViewset, base_name='api-commandes')
router.register(r'tags', views.TagsViewset, base_name='api-tags')
router.register(r'timeline', views.TimelineViewset, base_name='api-timeline')
router.register(r'user', views.BiblioUserViewset, base_name='api-user')
router.register(r'staff-commandes', views.CommandeStaffViewset, base_name='api-staff-commandes')
router.register(r'staff-commentaires', views.CommentaireStaffViewset, base_name='api-staff-commentaires')
router.register(r'staff-users', views.BiblioStaffUserViewset, base_name='api-staff-users')


urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
    # url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^logout/$', views.LogoutView.as_view(), {'next_page':"home"}, name='logout'),
    url(r'^accounts/signin/$', views.SigninView.as_view(), name='signin'),

    url(r'^json/panier/$', views.PanierJsonView.as_view(), name="panierjsonview"),
    url(r'^json/livre/$', views.LivreJsonView.as_view(), name="livrejsonview"),
    url(r'^json/lancement/$', views.LancementJsonView.as_view(), name="lancementjsonview"),
    url(r'^json/search/$', views.GlobalSearchJsonView.as_view(), name="globalsearchjsonview"),
    url(r'^json/profil/$', views.ProfilJsonView.as_view(), name="profiljsonview"),
    url(r'^json/staff/$', login_required(views.StaffJsonView.as_view()), name="staffjsonview"),

    url(r'^redactor/', include('redactor.urls')),

    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^profil/(?P<slug>[-\w]+)/$', views.ProfilView.as_view(), name='profil_detail'),
    url(r'^play/$', views.PlayView.as_view(), name='play'),
    url(r'^aide/$', views.AideView.as_view(), name='aide'),
    url(r'^pourquoi_bibliocratie/$', views.PourquoiBibliocratieView.as_view(), name='pourquoi_bibliocratie'),
    url(r'^mode_emploi/$', views.ModeEmploiView.as_view(), name='mode_emploi'),
    url(r'^confidentialite/$', views.ConfidentialiteView.as_view(), name='confidentialite'),
    url(r'^securite/$', views.SecuriteView.as_view(), name='securite'),
    url(r'^cgu/$', views.CGUView.as_view(), name='cgu'),
    url(r'^notifications/$', views.NotificationsView.as_view(), name='notifications'),
    url(r'^publications/$', views.LivreList.as_view(), name='livre_list'),
    url(r'^presouscriptions/$', views.PresouscriptionList.as_view(), name='presouscription_list'),
    url(r'^panier/$', views.PanierView.as_view(), name='panier'),
    url(r'^contact/$', views.ContactView.as_view(), name='contact'),
    url(r'^membres/$', views.MembresView.as_view(), name='membres'),
    url(r'^staff_only/$', views.StaffView.as_view(), name='staff_only'),

    url(r'^checkout/$', login_required(views.CheckoutView.as_view()), name='checkout'),
    url(r'^checkout/retourpayline/$', login_required(views.RetourPaylineView.as_view()), name='paylineretour'),
    url(r'^checkout/retourpaylinecancel/$', login_required(views.RetourPaylineView.as_view()), name='paylinecancel'),
    url(r'^checkout/paylinenotif/$', views.NotifPaylineView.as_view(), name='paylinenotif'),
    url(r'^lancement/$', views.LancementView.as_view(), name='lancement'),
    url(r'^lancement/interne/(?P<slug>[-\w]+)/$', login_required(views.LancementInterneView.as_view()), name='lancement_interne'),
    url(r'^lancement/couverture/(?P<slug>[-\w]+)/$', login_required(views.LancementCouvertureView.as_view()), name='lancement_couverture'),
    url(r'^lancement/prixdate/(?P<slug>[-\w]+)/$', login_required(views.LancementPrixdateView.as_view()), name='lancement_prixdate'),
    url(r'^lancement/debut/(?P<slug>[-\w]+)/$', login_required(views.LancementDebutView.as_view()), name='lancement_debut'),
    url(r'^lancement/vous/(?P<slug>[-\w]+)/$', login_required(views.LancementVousView.as_view()), name='lancement_vous'),
    url(r'^lancement/fin/(?P<slug>[-\w]+)/$', login_required(views.LancementFinView.as_view()), name='lancement_fin'),

    url(r'^produit/(?P<slug>[-\w]+)/$', RedirectView.as_view(pattern_name='livre_detail',permanent=True), name='livre_detail_wordpress'),
    url(r'^(?P<slug>[-\w]+)/$', views.LivreDetail.as_view(), name='livre_detail'),
    url(r'', include('django.contrib.auth.urls')),

    url(r'^crud/bibliouser/?$', views.BiblioUserView.as_view(), name='bibliouser_view'),
)

