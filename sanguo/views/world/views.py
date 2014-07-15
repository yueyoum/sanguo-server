# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/21/14'

import json

import arrow

from core.signals import login_signal
from core.item import Item
from core.exception import SanguoException

from core.attachment import get_drop_from_raw_package
from core.mail import Mail

from utils.decorate import message_response
from utils.api import api_activatecode_use, APIFailure

from libs import crypto, pack_msg
from libs.session import GameSession, session_dumps
from protomsg import SyncResponse, ResumeResponse

from preset.settings import ACTIVATECODE_MAIL_TITLE, ACTIVATECODE_MAIL_CONTENT
from preset import errormsg


@message_response("SyncResponse")
def sync(request):
    msg = SyncResponse()
    msg.ret = 0
    msg.utc_timestamp = arrow.utcnow().timestamp
    return pack_msg(msg)


@message_response("ResumeResponse")
def resume(request):
    req = request._proto
    sync = SyncResponse()
    sync.ret = 0
    sync.utc_timestamp = arrow.utcnow().timestamp

    login_signal.send(
        sender=None,
        char_id=request._char_id,
    )

    new_session = GameSession(request._account_id, req.server_id, request._char_id)
    new_session = crypto.encrypt(session_dumps(new_session))

    response = ResumeResponse()
    response.ret = 0
    return [pack_msg(response, new_session), pack_msg(sync)]



@message_response("SellResponse")
def sell(request):
    req = request._proto
    char_id = request._char_id

    item = Item(char_id)

    for ele in req.elements:
        # XXX
        if ele.tp == 1:
            print "NOT SUPPORT SELL HERO"
            continue

        if ele.tp == 2:
            print "NOT SUPPORT SELL SOUL"
            continue

        if ele.tp == 3:
            item.equip_sell([ele.id])
            continue

        if ele.tp == 4:
            item.gem_sell(ele.id, ele.amount)
            continue

        if ele.tp == 5:
            item.stuff_sell(ele.id, ele.amount)
            continue

    return None

@message_response("ActivateCodeUseResponse")
def activatecode_use(request):
    char_id = request._char_id
    code_id = request._proto.code_id

    data = {
        'char_id': char_id,
        'code_id': code_id
    }

    try:
        res = api_activatecode_use(data)
    except APIFailure:
        raise SanguoException(
            errormsg.SERVER_FAULT,
            char_id,
            "ActivateCode Use",
            "APIFailure. api_activatecode_use"
        )

    if res['ret'] != 0:
        raise SanguoException(
            res['ret'],
            char_id,
            "ActivateCode use",
            "api_activatecode_use ret = {0}".format(res['ret'])
        )

    # DONE
    package = res['data']['package']
    drop = get_drop_from_raw_package(package)

    mail = Mail(char_id)
    mail.add(
        ACTIVATECODE_MAIL_TITLE,
        ACTIVATECODE_MAIL_CONTENT,
        attachment=json.dumps(drop)
    )

    return None
