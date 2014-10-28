# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/25/14'

import sys

from core.character import Char
from core.msgpipe import publish_to_char
from core.activeplayers import ActivePlayers
from core.exception import SanguoException

from utils import pack_msg
from utils.api import api_system_broadcast_get, APIFailure
from preset.settings import CHAT_MESSAGE_MAX_LENGTH
from preset import errormsg

from protomsg import ChatMessageNotify, BroadcastNotify


class ChatMessagePublish(object):
    __slots__ = ['char_id', 'cache_char']
    def __init__(self, char_id):
        self.char_id = char_id
        self.cache_char = Char(char_id).mc

    def check(self, text):
        if len(text) > CHAT_MESSAGE_MAX_LENGTH:
            raise SanguoException(
                errormsg.CHAT_MESSAGE_TOO_LONG,
                self.char_id,
                "Chat",
                "message too long"
            )

    def to_char(self, target_char_id, text, check=True):
        if check:
            self.check(text)
        msg = ChatMessageNotify()
        chat_msg = msg.msgs.add()
        chat_msg.char.id = self.cache_char.id
        chat_msg.char.name = self.cache_char.name
        chat_msg.char.vip = self.cache_char.vip
        chat_msg.msg = text
        publish_to_char(target_char_id, pack_msg(msg))


    def to_server(self, text):
        self.check(text)
        ap = ActivePlayers()
        active_list = ap.get_list()
        for cid in active_list:
            self.to_char(cid, text, check=False)


class SystemBroadcast(object):
    def __init__(self, char_id):
        self.char_id = char_id

    def _fill_up_msg(self, msg, text, repeated_times):
        m = msg.msgs.add()
        m.text = text
        m.repeated_times = repeated_times

    def send_global_broadcast(self):
        try:
            data = api_system_broadcast_get({})
        except APIFailure:
            sys.stderr.write("API_SYSTEM_BROADCAST_GET FAILURE\n\n")
            return

        msg = BroadcastNotify()
        for item in data['data']:
            self._fill_up_msg(msg, item['content'], item['play_times'])

        publish_to_char(self.char_id, pack_msg(msg))

    def send_server_broadcast(self, text, repeated_times):
        pass

