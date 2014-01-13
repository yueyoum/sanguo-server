# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/13/14'

from settings import *
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP

ENABLE_ADMIN = True

USE_I18N = True
LANGUAGE_CODE = 'zh-CN'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'grappelli.dashboard',
    'grappelli',
    'django.contrib.admin',
) + INSTALLED_APPS


TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
)

GRAPPELLI_INDEX_DASHBOARD = 'dashboard.CustomIndexDashboard'


