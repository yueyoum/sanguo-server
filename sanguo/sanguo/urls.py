from django.conf import settings
from django.conf.urls import patterns, include, url

if settings.ENABLE_ADMIN:
    from django.contrib import admin
    admin.autodiscover()

from core.drives import redis_client
redis_client.ping()

import callbacks.signals


if settings.ENABLE_ADMIN:
    urlpatterns = patterns('',
                            url(r'^grappelli/', include('grappelli.urls')),
                            url(r'^admin/', include(admin.site.urls)),
                            )
else:
    urlpatterns = patterns('',
                           # Examples:
                           # url(r'^$', 'sanguo.views.home', name='home'),
                           # url(r'^sanguo/', include('sanguo.foo.urls')),

                           # Uncomment the admin/doc line below to enable admin documentation:
                           # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                           # Uncomment the next line to enable the admin:
                           # url(r'^admin/', include(admin.site.urls)),

                           url(r'', include('apps.account.urls')),
                           url(r'', include('apps.character.urls')),
                           url(r'', include('apps.item.urls')),
                           url(r'', include('apps.server.urls')),
                           url(r'', include('views.urls')),
    )

