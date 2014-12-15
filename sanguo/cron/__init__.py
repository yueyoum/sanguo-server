# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-15'

import os
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

for f in os.listdir(CURRENT_PATH):
    if f.endswith('.py') and f != '__init__.py':
        __import__('cron.{0}'.format(f[:-3]))
