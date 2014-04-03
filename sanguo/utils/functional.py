# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '3/11/14'

import random
from utils import timezone

from django.conf import settings
from core.drives import document_ids

NODE_ID = settings.NODE_ID

ID_MODULUS = 512

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


def id_generator(key, amount=1):
    addition = document_ids.inc(key, amount)
    addition_range = range(addition-amount+1, addition+1)
    return [ID_MODULUS*a+NODE_ID for a in addition_range]

