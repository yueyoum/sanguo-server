from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^equip/strengthen/$', views.strengthen_equip),
    url(r'^equip/sell/$', views.sell_equip),
    url(r'^equip/embed/$', views.embed),
    url(r'^equip/unembed/$', views.unembed),
)

