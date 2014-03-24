# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/21/14'

from core.signals import login_signal
from core.item import Item

from utils.decorate import message_response, operate_guard

from utils import timezone
from utils import pack_msg
from protomsg import SyncResponse

@message_response("SyncResponse")
@operate_guard('sync', 3, keep_result=False)
def sync(request):
    msg = SyncResponse()
    msg.ret = 0
    msg.utc_timestamp = timezone.utc_timestamp()
    return pack_msg(msg)


@message_response("ResumeResponse")
@operate_guard('resume', 3, keep_result=False)
def resume(request):
    login_signal.send(
        sender=None,
        account_id=request._account_id,
        server_id=request._server_id,
        char_id=request._char_id,
    )
    return None


@message_response("SellResponse")
def sell(request):
    req = request._proto
    char_id = request._char_id

    item = Item(char_id)

    for ele in req.elements:
        # XXX
        if ele.tp == 1:
            print "NOT SUPPORT SELL HERO"
            continue

        if ele.tp == 2:
            print "NOT SUPPORT SELL SOUL"
            continue

        if ele.tp == 3:
            item.equip_sell([ele.id])
            continue

        if ele.tp == 4:
            item.gem_remove(ele.id, ele.amount)
            continue

        if ele.tp == 5:
            item.stuff_remove(ele.id, ele.amount)
            continue

    return None
