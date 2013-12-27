from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
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

    url(r'', include('apps.player.urls')),
    url(r'', include('apps.character.urls')),
    url(r'', include('apps.item.urls')),
    
    url(r'^world/server-list/$', 'views.world.views.get_server_list'),
    
    url(r'^test/$', 'views.cmd.cmd'),

    url(r'^pve/$', 'views.stage.views.pve'),
    url(r'^pvp/$', 'views.stage.views.pvp'),

    url(r'^formation/set/$', 'views.formation.views.set_formation'),
    url(r'^socket/set/$', 'views.formation.views.set_socket'),
    url(r'^hero/get/$', 'views.hero.views.pick_hero'),
    url(r'^hero/merge/$', 'views.hero.views.merge_hero'),
    
    url(r'^gem/merge/$', 'views.gem.views.merge'),
    
    url(r'^hang/$', 'views.stage.views.hang'),
    url(r'^hang/cancel/$', 'views.stage.views.hang_cancel'),
    
    url(r'^prize/$', 'views.prize.views.prize_get'),
    
    url(r'^plunder/list/$', 'views.stage.views.plunder_list'),
    url(r'^plunder/$', 'views.stage.views.plunder'),
    
    url(r'^prison/open/$', 'views.prison.views.open_slot'),
    
    url(r'^prisoner/train/$', 'views.prison.views.train'),
    url(r'^prisoner/get/$', 'views.prison.views.get'),
)
