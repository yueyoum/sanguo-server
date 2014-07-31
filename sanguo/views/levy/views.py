# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/11/14'


from utils.decorate import message_response
from core.levy import Levy
from utils import pack_msg

from protomsg import LevyResponse

@message_response("LevyResponse")
def levy(request):
    l = Levy(request._char_id)
    gold = l.levy()
    msg = LevyResponse()
    msg.ret = 0
    msg.gold = gold

    return pack_msg(msg)
