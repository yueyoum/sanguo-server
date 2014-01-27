from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^hero/stepup/$', views.step_up),
                       )

