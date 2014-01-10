from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^world/server-list/$', views.get_server_list),
)
