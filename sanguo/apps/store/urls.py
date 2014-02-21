from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^store/panel/$', views.panel),
                       url(r'^store/buy/$', views.buy),
)
