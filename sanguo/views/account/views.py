# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'

import arrow

from core.exception import SanguoException
from core.signals import login_signal
from core.activeplayers import Player
from utils.decorate import message_response
from libs import crypto, pack_msg
from libs.session import GameSession, session_dumps

from protomsg import StartGameResponse, SyncResponse, BindAccountResponse
from utils.api import api_account_login, api_account_bind, APIFailure
from preset import errormsg

@message_response("StartGameResponse")
def login(request):
    req = request._proto
    data = {}
    data['server_id'] = req.server_id

    if req.regular.email:
        data['method'] = 'regular'
        data['name'] = req.regular.email
        data['password'] = req.regular.password
    else:
        data['method'] = 'anonymous'
        data['token'] = req.anonymous.device_token

    try:
        res = api_account_login(data)
    except APIFailure:
        raise SanguoException(
            errormsg.SERVER_FAULT,
            0,
            'Login',
            'APIFailure. api_account_login'
        )

    if res['ret'] != 0:
        raise SanguoException(
            res['ret'],
            0,
            'Login',
            'login, api_account_login, ret = {0}'.format(res['ret'])
        )

    account_id = res['data']['account_id']
    char_id = res['data']['char_id']
    new_token = res['data']['new_token']

    request._account_id = account_id
    request._server_id = req.server_id

    login_signal.send(
        sender=None,
        char_id=char_id
    )

    if char_id:
        request._char_id = char_id
    else:
        request._char_id = None

    session = GameSession(request._account_id, request._server_id, request._char_id)

    if char_id:
        Player(char_id).set_login_id(session.login_id)

    request._game_session = session
    session = crypto.encrypt(session_dumps(session))

    response = StartGameResponse()
    response.ret = 0
    if req.regular.email:
        response.regular.MergeFrom(req.regular)
    else:
        response.anonymous.device_token = str(new_token)

    response.need_create_new_char = char_id == 0

    sync = SyncResponse()
    sync.ret = 0
    sync.utc_timestamp = arrow.utcnow().timestamp

    return [pack_msg(response, session), pack_msg(sync)]



@message_response("BindAccountResponse")
def bind(request):
    req = request._proto
    data = {
        'name': req.email,
        'password': req.password,
        'token': req.device_token
    }

    try:
        res = api_account_bind(data)
    except APIFailure:
        raise SanguoException(
            errormsg.SERVER_FAULT,
            request._char_id,
            'Account Bind',
            'APIFailure. api_account_bind'
        )

    if res['ret'] != 0:
        raise SanguoException(
            res['ret'],
            request._char_id,
            'Account Bind',
            'api_account_bind, ret = {0}'.format(res['ret'])
        )

    response = BindAccountResponse()
    response.ret = 0
    response.email = req.email
    response.password = req.password

    return pack_msg(response)
