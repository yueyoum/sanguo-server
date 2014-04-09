# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'


from core.exception import SanguoException
from core.signals import login_signal
from protomsg import CreateCharacterResponse
from utils import crypto, pack_msg
from utils.decorate import message_response


from utils.api import api_character_create

# ONLY GUIDE SERVER WILL CALL THIS VIEW FUNCTION
@message_response("CreateCharacterResponse")
def create_character(request):
    req = request._proto

    data = {
        'account_id': request._account_id,
        'server_id': request._server_id,
        'name': req.name
    }

    res = api_character_create(data)
    print "CREATE CHARACTER"
    print res

    # FIXME
    ret_table = {
        30: 202,
        31: 200,
        32: 201,
    }

    if res['ret'] != 0:
        raise SanguoException(ret_table[res['ret']])

    char_id = res['data']['char_id']

    login_signal.send(
        sender=None,
        account_id=request._account_id,
        server_id=request._server_id,
        char_id=char_id
    )

    request._char_id = char_id

    # new_session = '%s:%d' % (request._session, char_id)
    new_session = '%d:0:%d' % (request._account_id, char_id)
    new_session = crypto.encrypt(new_session)

    response = CreateCharacterResponse()
    response.ret = 0
    return pack_msg(response, new_session)
