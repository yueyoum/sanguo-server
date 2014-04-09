# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'

# -*- coding: utf-8 -*-

from utils.decorate import message_response

from core.store import Store
from utils import pack_msg

from protomsg import StorePanelResponse, StoreBuyResponse

@message_response("StorePanelResponse")
def panel(request):
    s = Store(request._char_id)
    msg = s.fill_up_notify_msg()
    response = StorePanelResponse()
    response.ret = 0
    response.panel.MergeFrom(msg)
    return pack_msg(response)


@message_response("StoreBuyResponse")
def buy(request):
    s = Store(request._char_id)
    s.buy(request._proto.id, request._proto.amount)
    return None

