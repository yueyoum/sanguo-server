# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/25/14'

from core.character import Char
from core.msgpipe import publish_to_char
from core.activeplayers import ActivePlayers

from utils import pack_msg

from protomsg import ChatMessageNotify, BroadcastNotify


class ChatMessagePublish(object):
    def __init__(self, server_id, char_id):
        self.char_id = char_id
        self.server_id = server_id

        self.cache_char = Char(char_id).cacheobj

    def to_char(self, target_char_id, text):
        msg = ChatMessageNotify()
        chat_msg = msg.msgs.add()
        chat_msg.char.id = self.cache_char.id
        chat_msg.char.name = self.cache_char.name
        chat_msg.char.official = self.cache_char.official
        chat_msg.msg = text.encode('utf-8')
        publish_to_char(target_char_id, pack_msg(msg))

    def to_server(self, text):
        ap = ActivePlayers(self.server_id)
        active_list = ap.get_list()
        for cid in active_list:
            self.to_char(cid, text)


class BroadcastMessagePublish(object):
    def to_server(self, server_id, tid, *args):
        ap = ActivePlayers(server_id)
        active_list = ap.get_list()

        for cid in active_list:
            msg = BroadcastNotify()
            b_msg = msg.msgs.add()
            b_msg.id = tid
            for a in args:
                b_msg.args.append(a.encode('utf-8'))

            publish_to_char(cid, pack_msg(msg))
