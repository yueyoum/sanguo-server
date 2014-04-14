# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/11/14'


from utils.decorate import message_response
from core.levy import Levy

@message_response("LevyResponse")
def levy(request):
    l = Levy(request._char_id)
    l.levy()
    return None
