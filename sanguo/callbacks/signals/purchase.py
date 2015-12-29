# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '15-2-9'

import arrow

from core.signals import new_purchase_signal
from core.vip import VIP
from core.mongoscheme import MongoPurchaseLog
from core.activity import ActivityStatic, ActivityEntry


def _new_purchase(char_id, new_got, total_got, **kwargs):
    VIP(char_id).send_notify()

    plog = MongoPurchaseLog()
    plog.char_id = char_id
    plog.sycee = new_got
    plog.purchase_at = arrow.utcnow().timestamp
    plog.save()

    ActivityStatic(char_id).trig(5001)
    ActivityStatic(char_id).trig(14001)
    ActivityEntry(char_id, 16001).trig(new_got/2)
    ActivityEntry(char_id, 17001).trig()
    ActivityEntry(char_id, 17002).trig()

    ActivityEntry(char_id, 999).trig()
    ActivityEntry(char_id, 1000).trig()


new_purchase_signal.connect(
    _new_purchase,
    dispatch_uid='callbacks.signals.vip._new_purchase'
)

