from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sanguo.views.home', name='home'),
    # url(r'^sanguo/', include('sanguo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'', include('apps.player.urls')),
    url(r'', include('apps.world.urls')),
    url(r'', include('apps.character.urls')),

    url(r'^pve/$', 'views.battle.pve'),
    url(r'^formation/set/$', 'views.formation.set_formation'),
    url(r'^socket/set/$', 'views.formation.set_socket'),
    url(r'^hero/get/$', 'views.hero.pick_hero'),
    url(r'^hero/merge/$', 'views.hero.merge_hero'),
)
