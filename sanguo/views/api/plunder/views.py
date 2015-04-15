# -*- coding: utf-8 -*-
"""
Author:         Wang Chao <yueyoum@gmail.com>
Filename:       views
Date Created:   2015-04-15 10:47
Description:

"""
import json

from utils.decorate import json_return
from core.plunder import PlunderRival
from core.affairs import Affairs

@json_return
def search(request):
    city_id = int(request.POST['city_id'])
    exclude_char_id = int(request.POST['exclude_char_id'])

    target = PlunderRival.search(city_id, exclude_char_id=exclude_char_id, return_dumps=True)
    return {
        'ret': 0,
        'data': target
    }

@json_return
def finish(request):
    from_char_id = int(request.POST['from_char_id'])
    from_char_name = request.POST['from_char_name']
    to_char_id = int(request.POST['to_char_id'])
    from_win = request.POST['from_win'] == '1'
    standard_drop = json.loads(request.POST['standard_drop'])

    affairs = Affairs(to_char_id)
    affairs.got_plundered(from_char_id, from_char_name, from_win, standard_drop)
