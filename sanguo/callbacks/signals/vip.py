# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-14'

from core.signals import vip_changed_signal
from core.prison import Prison
from core.mail import Mail
from core.plunder import Plunder
from core.activity import ActivityStatic, has_activity, ActivityEntry
from preset.settings import MAIL_VIP_CHANGED_CONTENT, MAIL_VIP_CHANGED_TITLE
from preset.data import VIP_FUNCTION


def _vip_change(char_id, old_vip, new_vip, **kwargs):
    Prison(char_id).vip_changed(new_vip)
    m = Mail(char_id)
    m.add(name=MAIL_VIP_CHANGED_TITLE, content=MAIL_VIP_CHANGED_CONTENT.format(new_vip))

    # 增加掠夺次数
    plunder_times_change_value = VIP_FUNCTION[new_vip].plunder - VIP_FUNCTION[old_vip].plunder
    if plunder_times_change_value:
        plunder = Plunder(char_id)
        plunder.change_current_plunder_times(plunder_times_change_value, allow_overflow=True)

    vip_activies = []
    if has_activity(22001):
        vip_activies.append(22001)
    if has_activity(40007):
        vip_activies.append(40007)
    if has_activity(40008):
        vip_activies.append(40008)
    if has_activity(50006):
        vip_activies.append(50006)

    if vip_activies:
        ActivityStatic(char_id).send_update_notify(activity_ids=vip_activies)

    ae = ActivityEntry(char_id, 50006)
    if ae and ae.is_valid():
        ae.enable(new_vip)
        ActivityStatic(char_id).send_update_notify(activity_ids=[50006])

vip_changed_signal.connect(
    _vip_change,
    dispatch_uid='callbacks.signals.vip._vip_up'
)

