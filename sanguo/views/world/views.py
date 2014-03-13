# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/21/14'

from core.signals import login_signal

from utils.decorate import message_response, operate_guard

from utils import timezone
from utils import pack_msg
from protomsg import SyncResponse

@message_response("SyncResponse")
@operate_guard('sync', 3, keep_result=False)
def sync(request):
    msg = SyncResponse()
    msg.ret = 0
    msg.utc_timestamp = timezone.utc_timestamp()
    return pack_msg(msg)


@message_response("ResumeResponse")
@operate_guard('resume', 3, keep_result=False)
def resume(request):
    login_signal.send(
        sender=None,
        account_id=request._account_id,
        server_id=request._server_id,
        char_id=request._char_id,
    )

