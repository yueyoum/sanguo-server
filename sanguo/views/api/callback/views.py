# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-9'


import json
from django.http import HttpResponse

from core.stage import Hang

def timer_notify(request):
    data = request.body
    data = json.loads(data)

    h = Hang(data['char_id'])
    h.timer_notify(data['seconds'])
    return HttpResponse(json.dumps({'ret': 0}), content_type='application/json')
