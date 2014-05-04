# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'

from core.exception import SanguoException
from core.signals import login_signal
from utils.decorate import message_response
from utils import timezone
from libs import crypto, pack_msg

from protomsg import StartGameResponse, SyncResponse

from utils.api import api_account_login

@message_response("StartGameResponse")
def login(request):
    req = request._proto
    # FIXME
    data = {}
    data['server_id'] = req.server_id
    if req.anonymous.device_token:
        data['method'] = 'anonymous'
        data['token'] = req.anonymous.device_token
    else:
        data['method'] = 'regular'
        data['name'] = req.regular.email
        data['password'] = req.regular.password

    res = api_account_login(data)

    if res['ret'] != 0:
        raise SanguoException(
            res['ret'],
            0,
            'Login',
            'login, api_account_login, ret = {0}'.format(res['ret'])
        )

    account_id = res['data']['account_id']
    char_id = res['data']['char_id']

    request._account_id = account_id
    request._server_id = req.server_id

    login_signal.send(
        sender=None,
        account_id=request._account_id,
        server_id=request._server_id,
        char_id=char_id
    )

    if char_id:
        request._char_id = char_id
        session_str = '{0}:{1}:{2}'.format(
            request._account_id,
            request._server_id,
            request._char_id
        )
    else:
        request._char_id = None
        session_str = '{0}:{1}'.format(request._account_id, request._server_id)

    session = crypto.encrypt(session_str)

    response = StartGameResponse()
    response.ret = 0
    if req.anonymous.device_token:
        response.anonymous.MergeFrom(req.anonymous)
    else:
        response.regular.MergeFrom(req.regular)
    response.need_create_new_char = char_id == 0

    sync = SyncResponse()
    sync.ret = 0
    sync.utc_timestamp = timezone.utc_timestamp()

    return [pack_msg(response, session), pack_msg(sync)]
