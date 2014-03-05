# -*- coding: utf-8 -*-

from django.db import IntegrityError

from apps.character.models import Character
from core.exception import SanguoException
from core.signals import login_signal
from protomsg import CreateCharacterResponse
from utils import crypto, pack_msg
from utils.decorate import message_response

from core.character import char_initialize


@message_response("CreateCharacterResponse")
def create_character(request):
    req = request._proto

    if len(req.name) > 7:
        raise SanguoException(202, "Create Char: name too long. {0}".format(req.name))

    account_id, server_id = request._account_id, request._server_id

    if Character.objects.filter(account_id=account_id, server_id=server_id).exists():
        raise SanguoException(200, "Create Char: Account {0} already has a char in Server {1}".format(account_id, server_id))


    try:
        char = char_initialize(account_id, server_id, req.name)
    except IntegrityError as e:
        raise SanguoException(201, "Create Char. ERROR: {0}".format(str(e)))


    login_signal.send(
        sender=None,
        account_id=account_id,
        server_id=server_id,
        char_id=char.id
    )

    request._char_id = char.id

    new_session = '%s:%d' % (request._session, char.id)
    new_session = crypto.encrypt(new_session)

    response = CreateCharacterResponse()
    response.ret = 0
    return pack_msg(response, new_session)
