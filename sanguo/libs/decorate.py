# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/17/14'

import json
from django.http import HttpResponse


def json_return(func):
    def wrap(*args, **kwargs):
        res = func(*args, **kwargs)
        if isinstance(res, dict):
            return HttpResponse(json.dumps(res), content_type='application/json')
        return res
    return wrap
