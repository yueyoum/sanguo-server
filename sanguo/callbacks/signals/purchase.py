# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '15-2-9'

import arrow

from core.signals import new_purchase_signal
from core.vip import VIP
from core.mongoscheme import MongoPurchaseLog
from core.activity import ActivityStatic


def _new_purchase(char_id, new_got, total_got, **kwargs):
    VIP(char_id).send_notify()

    plog = MongoPurchaseLog()
    plog.char_id = char_id
    plog.sycee = new_got
    plog.purchase_at = arrow.utcnow()
    plog.save()

    ActivityStatic(char_id).trig(5001)



new_purchase_signal.connect(
    _new_purchase,
    dispatch_uid='callbacks.signals.vip._new_purchase'
)

