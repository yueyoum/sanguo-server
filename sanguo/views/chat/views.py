# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/25/14'

from core.msgpublish import ChatMessagePublish
from core.exception import InvalidOperate
from utils.decorate import message_response


MSG_LEN_MAX = 50

@message_response("ChatSendResponse")
def send(request):
    req = request._proto
    msg = req.msg
    if len(msg) > MSG_LEN_MAX:
        raise InvalidOperate("Chat Messaget too long!")

    server_id = request._server_id
    char_id = request._char_id

    cp = ChatMessagePublish(server_id, char_id)
    cp.to_server(req.msg)
    return None
