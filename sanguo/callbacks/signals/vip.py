# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-14'

from core.signals import vip_changed_signal
from core.prison import Prison

def _vip_change(char_id, old_vip, new_vip, **kwargs):
    Prison(char_id).vip_changed(new_vip)


vip_changed_signal.connect(
    _vip_change,
    dispatch_uid='callbacks.signals.vip._vip_up'
)
