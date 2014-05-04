# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/25/14'

from core.msgpublish import ChatMessagePublish
from core.exception import SanguoException
from utils.decorate import message_response, operate_guard
from preset import errormsg


MSG_LEN_MAX = 50

@message_response("ChatSendResponse")
@operate_guard('chat', 15, keep_result=False)
def send(request):
    req = request._proto
    msg = req.msg
    if len(msg) > MSG_LEN_MAX:
        raise SanguoException(
            errormsg.CHAT_MESSAGE_TOO_LONG,
            request._char_id,
            "Chat",
            "message too long"
        )

    server_id = request._server_id
    char_id = request._char_id

    cp = ChatMessagePublish(server_id, char_id)
    cp.to_server(req.msg)
    return None
