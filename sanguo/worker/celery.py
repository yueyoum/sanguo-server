# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '5/20/14'

from __future__ import absolute_import
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanguo.settings')


app = Celery('sanguo')
app.config_from_object('django.conf:settings')


if __name__ == '__main__':
    app.start()
