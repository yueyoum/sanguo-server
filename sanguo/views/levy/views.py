# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/11/14'


from utils.decorate import message_response
from core.levy import Levy
from core.attachment import standard_drop_to_attachment_protomsg
from utils import pack_msg

from protomsg import LevyResponse

@message_response("LevyResponse")
def levy(request):
    l = Levy(request._char_id)
    drop = l.levy()
    msg = LevyResponse()
    msg.ret = 0
    msg.drop.MergeFrom(standard_drop_to_attachment_protomsg(drop))

    return pack_msg(msg)
