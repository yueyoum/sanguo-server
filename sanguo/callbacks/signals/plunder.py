# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-9-18'


from core.signals import plunder_finished_signal
from core.affairs import Affairs

def _plunder_finished(from_char_id, to_char_id, from_win, standard_drop, **kwargs):
    affairs = Affairs(to_char_id)
    affairs.got_plundered(from_char_id, from_win, standard_drop)


plunder_finished_signal.connect(
    _plunder_finished,
    dispatch_uid='callbacks.signals.plunder._plunder_finished'
)
