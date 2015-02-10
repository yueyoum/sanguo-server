# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '15-2-10'

from core.signals import heropanel_open_hero_signal

from core.activity import ActivityEntry
from core.attachment import is_empty_drop, standard_drop_to_attachment_protomsg
from core.msgpipe import publish_to_char
from utils import pack_msg


def _open_hero(char_id, hero_oid, **kwargs):
    drop = ActivityEntry(9001).get_additional_drop()
    if is_empty_drop(drop):
        return

    publish_to_char(char_id, pack_msg(standard_drop_to_attachment_protomsg(drop)))



heropanel_open_hero_signal.connect(
    _open_hero,
    dispatch_uid='callbacks.signals.heropanel._open_hero'
)
