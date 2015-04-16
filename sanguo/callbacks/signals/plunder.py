# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-9-18'

import json

from core.signals import plunder_finished_signal

from utils.api import apicall

def _plunder_finished(from_char_id, from_char_name, to_char_id, from_win, standard_drop, target_server_url, **kwargs):
    data = {
        'from_char_id': from_char_id,
        'from_char_name': from_char_name,
        'to_char_id': to_char_id,
        'from_win': 1 if from_win else 0,
        'standard_drop': json.dumps(standard_drop)
    }

    cmd = target_server_url + "/api/plunder/finish/"
    apicall(data=data, cmd=cmd)


plunder_finished_signal.connect(
    _plunder_finished,
    dispatch_uid='callbacks.signals.plunder._plunder_finished'
)
