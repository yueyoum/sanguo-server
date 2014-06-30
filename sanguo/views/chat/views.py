# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/25/14'

from core.msgpublish import ChatMessagePublish
from utils.decorate import message_response, operate_guard
from preset.settings import OPERATE_INTERVAL_CHAT_SEND


@message_response("ChatSendResponse")
@operate_guard('chat', OPERATE_INTERVAL_CHAT_SEND, keep_result=False)
def send(request):
    req = request._proto
    char_id = request._char_id

    cp = ChatMessagePublish(char_id)
    cp.to_server(req.msg)
    return None
