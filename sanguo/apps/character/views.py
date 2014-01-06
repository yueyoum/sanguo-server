# -*- coding: utf-8 -*-
import logging

from apps.character.models import Character
from core.exception import SanguoException
from core.signals import login_signal
from protomsg import CreateCharacterResponse
from utils import crypto, pack_msg
from utils.decorate import message_response

from core.character import Char

logger = logging.getLogger('sanguo')


@message_response("CreateCharacterResponse")
def create_character(request):
    req = request._proto

    if len(req.name) > 7:
        logger.warning("Create Char: name too long. {0}".format(req.name))
        raise SanguoException(202)

    account_id, server_id = request._account_id, request._server_id

    if Character.objects.filter(account_id=account_id, server_id=server_id).exists():
        logger.warning("Create Char: Account {0} already has a char in Server {1}".format(account_id, server_id))
        raise SanguoException(200)

    if Character.objects.filter(server_id=server_id, name=req.name).exists():
        logger.warning("Create Char: Duplicated name {0} in Server {1}".format(req.name, server_id))
        raise SanguoException(201)

    char = Char(
        account_id=account_id,
        server_id=server_id,
        name=req.name
    )

    login_signal.send(
        sender=None,
        account_id=account_id,
        server_id=server_id,
        char_id=char.id
    )

    #char_created_signal.send(
    #    sender = None,
    #    account_id = account_id,
    #    server_id = server_id,
    #    char_obj = char
    #)

    request._char_id = char.id

    new_session = '%s:%d' % (request._session, char.id)
    new_session = crypto.encrypt(new_session)

    response = CreateCharacterResponse()
    response.ret = 0
    return pack_msg(response, new_session)
