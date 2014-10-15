# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-14'

from core.signals import vip_changed_signal, new_purchase_signal
from core.prison import Prison
from core.vip import VIP

def _new_purchase(char_id, new_got, total_got, **kwargs):
    VIP(char_id).send_notify()

def _vip_change(char_id, old_vip, new_vip, **kwargs):
    Prison(char_id).vip_changed(new_vip)


vip_changed_signal.connect(
    _vip_change,
    dispatch_uid='callbacks.signals.vip._vip_up'
)

new_purchase_signal.connect(
    _new_purchase,
    dispatch_uid='callbacks.signals.vip._new_purchase'
)

