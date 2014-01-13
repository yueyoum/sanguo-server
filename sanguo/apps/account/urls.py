from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^player/login/$', views.login),
                       url(r'^player/register/$', views.register),
)
