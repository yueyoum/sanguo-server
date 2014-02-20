from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^pve/$', views.pve),
                       url(r'^hang/$', views.hang_start),
                       url(r'^hang/cancel/$', views.hang_cancel),
                       url(r'^elitepve/$', views.elite_pve),
)
