# -*- coding: utf-8 -*-
import re
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

from django.contrib import admin
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns

try:
    from django import setup
except ImportError:
    def setup():
        pass

urlpatterns = patterns('',
    # The Django admin is not officially supported; expect breakage.
    # Nonetheless, it's often useful for debugging.
    url(r'^r2d2/', include(admin.site.urls)),
    url(r'^redactor/', include('redactor.urls')),
    url(r'^rest-auth/', include('rest_auth.urls')),
    # url(r'^rest-auth/registration/', include('rest_auth.registration.urls'))
    #etherpad
    # url(r'^', include('etherpadlite.urls')),
)

urlpatterns += i18n_patterns(
    url(r'^', include('bibliocratie.urls')),
)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('rosetta.urls')),
    )

#serving media files in dev
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

