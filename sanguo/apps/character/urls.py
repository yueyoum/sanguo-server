from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^char/create/$', views.create_character),
    url(r'^hero/get/$', views.get_hero),
    url(r'^hero/merge/$', views.merge_hero),
)

