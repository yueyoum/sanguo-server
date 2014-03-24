from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^equip/strengthen/$', views.strengthen_equip),
                       url(r'^equip/stepup/$', views.step_up_equip),
                       url(r'^equip/embed/$', views.embed),
                       url(r'^equip/unembed/$', views.unembed),
                       url(r'^equip/specialbuy/$', views.special_buy),
                       url(r'^gem/merge/$', views.merge),
)

