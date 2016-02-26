# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'


from core.exception import SanguoException
from core.signals import login_signal
from core.server import server
from core.character import char_initialize
from core.activeplayers import Player
from protomsg import CreateCharacterResponse
from libs import crypto, pack_msg
from libs.session import session_dumps

from utils.decorate import message_response
from utils.api import api_character_create, api_character_failure


@message_response("CreateCharacterResponse")
def create_character(request):
    req = request._proto

    data = {
        'account_id': request._account_id,
        'server_id': server.id,
        'name': req.name
    }

    res = api_character_create(data)
    if res['ret'] != 0:
        raise SanguoException(
            res['ret'],
            0,
            'Character Create',
            'api_character_create, ret = {0}'.format(res['ret'])
        )

    char_id = res['data']['char_id']
    try:
        char_initialize(request._account_id, server.id, char_id, req.name)
    except Exception as e:
        data = {
            'char_id': char_id,
        }
        api_character_failure(data)
        raise e

    login_signal.send(
        sender=None,
        char_id=char_id,
        real_login=True,
    )

    request._char_id = char_id

    game_session = request._game_session
    game_session.char_id = char_id

    new_session = crypto.encrypt(session_dumps(game_session))

    Player(char_id).set_login_id(game_session.login_id)

    response = CreateCharacterResponse()
    response.ret = 0
    return pack_msg(response, new_session)
