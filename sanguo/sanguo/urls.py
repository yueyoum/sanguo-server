from django.conf import settings
from django.conf.urls import patterns, include, url


from core.drives import redis_client
redis_client.ping()

import callbacks.signals

urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'sanguo.views.home', name='home'),
                       # url(r'^sanguo/', include('sanguo.foo.urls')),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       # url(r'^admin/', include(admin.site.urls)),
                       url(r'', include('views.urls')),
)

