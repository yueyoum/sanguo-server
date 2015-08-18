# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/25/14'

import sys
import cPickle

from core.drives import redis_client
from core.character import Char
from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.server import server

from utils import pack_msg
from utils.api import api_system_broadcast_get, APIFailure
from preset.settings import CHAT_MESSAGE_MAX_LENGTH
from preset import errormsg

from tasks import world

from protomsg import ChatMessageNotify, BroadcastNotify, ChatMessage


class GlobalChatQueue(object):
    REDIS_KEY = 'global_chat_queue:{0}'.format(server.id)
    QUEUE_SIZE = 20
    @classmethod
    def put(cls, data):
        while redis_client.llen(cls.REDIS_KEY) >= cls.QUEUE_SIZE:
            redis_client.lpop(cls.REDIS_KEY)

        redis_client.rpush(cls.REDIS_KEY, data)

    @classmethod
    def get(cls):
        return redis_client.lrange(cls.REDIS_KEY, 0, -1)



class ChatMessagePublish(object):
    def __init__(self, char_id):
        self.char_id = char_id

    def check(self, text):
        if len(text) > CHAT_MESSAGE_MAX_LENGTH:
            raise SanguoException(
                errormsg.CHAT_MESSAGE_TOO_LONG,
                self.char_id,
                "Chat",
                "message too long"
            )


    def send_notify(self):
        msgs = GlobalChatQueue.get()
        if not msgs:
            return

        msg = ChatMessageNotify()
        for x in msgs:
            msg_x = msg.msgs.add()
            msg_x.MergeFromString(x)

        publish_to_char(self.char_id, pack_msg(msg))



    def to_server(self, text):
        self.check(text)

        cache_char = Char(self.char_id).mc

        msg = ChatMessage()
        msg.char.id = cache_char.id
        msg.char.name = cache_char.name
        msg.char.vip = cache_char.vip
        msg.msg = text

        data = msg.SerializeToString()
        GlobalChatQueue.put(data)

        # broadcast to all characters
        notify = ChatMessageNotify()
        notify_msg = notify.msgs.add()
        notify_msg.MergeFrom(msg)

        notify_bin = pack_msg(notify)

        arg = {'msg': notify_bin}
        data = cPickle.dumps(arg)
        world.broadcast(data=data)


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

