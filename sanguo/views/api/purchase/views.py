# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/21/14'


from utils.decorate import json_return

from core.character import Char

@json_return
def purchase_done(request):
    try:
        char_id = int(request.POST['char_id'])
        sycee = int(request.POST['sycee'])
    except (KeyError, ValueError):
        return {'ret': 1}

    c = Char(char_id)
    c.update(sycee=sycee, des='Purchase')
    return {'ret': 0}

