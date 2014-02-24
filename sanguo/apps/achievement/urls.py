from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^achievement/getreward/$', views.get_reward),
)
