# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '3/11/14'

import random
from utils import timezone


def timebased_unique_id(tz='local'):
    if tz == 'local':
        now = timezone.localnow()
    else:
        now = timezone.utcnow()

    return '{0}-{1}-{2}'.format(
        now.strftime('%Y%m%d_%H%M%S'),
        random.randint(10000, 99999),
        random.randint(10000, 99999),
    )
