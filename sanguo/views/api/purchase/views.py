# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/21/14'


from utils.decorate import json_return

from core.resource import Resource


@json_return
def purchase_done(request):
    try:
        char_id = int(request.POST['char_id'])
        sycee = int(request.POST['sycee'])
        actual_sycee = int(request.POST['actual_sycee'])
    except (KeyError, ValueError):
        return {'ret': 1}

    resource = Resource(char_id, "Purchase Done", "purchase got: sycee {0}, actual sycee {1}".format(sycee, actual_sycee))
    resource.add(purchase_got=sycee, purchase_actual_got=actual_sycee)
    return {'ret': 0}
