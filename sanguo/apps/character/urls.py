from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^char/create/$', views.create_character),
)

