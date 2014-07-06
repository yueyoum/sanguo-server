# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-6'

from django.conf import settings
from core.drives import document_ids

SERVER_ID = settings.SERVER_ID
ID_MODULUS = 512
# servers amount MUST <= 512

def id_generator(key, amount=1):
    addition = int(document_ids.inc(key, amount))
    addition_range = range(addition-amount+1, addition+1)
    return [ID_MODULUS*a+SERVER_ID for a in addition_range]
