# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-14'

from core.signals import vip_changed_signal, new_purchase_signal
from core.prison import Prison
from core.vip import VIP
from core.mail import Mail
from core.plunder import Plunder
from preset.settings import MAIL_VIP_CHANGED_CONTENT, MAIL_VIP_CHANGED_TITLE
from preset.data import VIP_FUNCTION

def _new_purchase(char_id, new_got, total_got, **kwargs):
    VIP(char_id).send_notify()

def _vip_change(char_id, old_vip, new_vip, **kwargs):
    Prison(char_id).vip_changed(new_vip)
    m = Mail(char_id)
    m.add(name=MAIL_VIP_CHANGED_TITLE, content=MAIL_VIP_CHANGED_CONTENT.format(new_vip))

    # 增加掠夺次数
    plunder_times_change_value = VIP_FUNCTION[new_vip].plunder - VIP_FUNCTION[old_vip].plunder
    if plunder_times_change_value:
        plunder = Plunder(char_id)
        plunder.change_current_plunder_times(plunder_times_change_value, allow_overflow=True)


vip_changed_signal.connect(
    _vip_change,
    dispatch_uid='callbacks.signals.vip._vip_up'
)

new_purchase_signal.connect(
    _new_purchase,
    dispatch_uid='callbacks.signals.vip._new_purchase'
)

