# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/25/14'

import sys

from core.drives import redis_client
from core.mongoscheme import MongoCharacter
from core.character import Char
from core.msgpipe import publish_to_char
from core.exception import SanguoException

from utils import pack_msg
from utils.api import api_system_broadcast_get, APIFailure
from preset.settings import CHAT_MESSAGE_MAX_LENGTH
from preset import errormsg

from protomsg import ChatMessageNotify, BroadcastNotify, ChatMessage


class ChatMessagePublish(object):
    __slots__ = ['char_id', 'cache_char', 'redis_key']
    REDIS_KEY_TEMPLATE = 'chat_queue:{0}'
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

    def send_notify(self):
        msgs = redis_client.lrange(self.REDIS_KEY_TEMPLATE.format(self.char_id), 0, -1)
        if not msgs:
            return

        redis_client.delete(self.REDIS_KEY_TEMPLATE.format(self.char_id))

        msg = ChatMessageNotify()
        for x in msgs:
            msg_x = msg.msgs.add()
            msg_x.MergeFromString(x)

        publish_to_char(self.char_id, pack_msg(msg))

    def put_in_char_msg_queue(self, target_char_id, text, check=True):
        if check:
            self.check(text)
        msg = ChatMessage()
        msg.char.id = self.cache_char.id
        msg.char.name = self.cache_char.name
        msg.char.vip = self.cache_char.vip
        msg.msg = text

        redis_key = self.REDIS_KEY_TEMPLATE.format(target_char_id)

        while redis_client.llen(redis_key) >= 20:
            redis_client.lpop(redis_key)

        redis_client.rpush(redis_key, msg.SerializeToString())


    def to_server(self, text):
        self.check(text)
        chars = MongoCharacter.objects.all()
        for c in chars:
            self.put_in_char_msg_queue(c.id, text, check=False)


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

