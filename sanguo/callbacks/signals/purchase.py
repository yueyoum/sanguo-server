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

    # 需要发送活动通知的， 就必须用 ActivityStatic trig
    acs = ActivityStatic(char_id)
    acs.trig(5001)
    acs.trig(14001)
    ActivityEntry(char_id, 16001).trig(new_got/2)
    ActivityEntry(char_id, 17001).trig()
    ActivityEntry(char_id, 17002).trig()

    acs.trig(18006)

    ActivityEntry(char_id, 999).trig()
    ActivityEntry(char_id, 1000).trig()

    acs.trig(19001)
    acs.trig(20001)

    if ActivityEntry(char_id, 30006).trig(new_got):
        acs.send_update_notify(activity_ids=[30006])

    ActivityEntry(char_id, 4000).trig()

new_purchase_signal.connect(
    _new_purchase,
    dispatch_uid='callbacks.signals.vip._new_purchase'
)

