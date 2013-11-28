from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^equipment/strengthen/$', views.strengthen_equip),
    url(r'^equipment/sell/$', views.sell_equip),
)

