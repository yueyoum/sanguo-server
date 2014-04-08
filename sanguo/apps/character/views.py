# -*- coding: utf-8 -*-

from django.db import IntegrityError

from apps.character.models import Character
from core.exception import SanguoException
from core.signals import login_signal
from protomsg import CreateCharacterResponse
from utils import crypto, pack_msg
from utils.decorate import message_response

# from core.character import char_create, char_initialize


# @message_response("CreateCharacterResponse")
# def create_character(request):
#     req = request._proto
#
#     account_id, server_id = request._account_id, request._server_id
#
#     char_id = char_create(account_id, server_id, req.name)
#     char_initialize(char_id)
#
#     login_signal.send(
#         sender=None,
#         account_id=account_id,
#         server_id=server_id,
#         char_id=char_id
#     )
#
#     request._char_id = char_id
#
#     new_session = '%s:%d' % (request._session, char_id)
#     new_session = crypto.encrypt(new_session)
#
#     response = CreateCharacterResponse()
#     response.ret = 0
#     return pack_msg(response, new_session)
#
# from utils.api import api_character_create
#
# @message_response("CreateCharacterResponse")
# def create_character(request):
#     req = request._proto
#
#     data = {
#         'account_id': request._account_id,
#         'server_id': request._server_id,
#         'name': req.name
#     }
#
#     res = api_character_create(data)
#     print "CREATE CHARACTER"
#     print res
#
#     # FIXME
#     ret_table = {
#         30: 202,
#         31: 200,
#         32: 201,
#     }
#
#     if res['ret'] != 0:
#         raise SanguoException(ret_table[res['ret']])
#
#     char_id = res['data']['char_id']
#
#     # login_signal.send(
#     #     sender=None,
#     #     account_id=req._account_id,
#     #     server_id=req._server_id,
#     #     char_id=char_id
#     # )
#
#     request._char_id = char_id
#
#     new_session = '%s:%d' % (request._session, char_id)
#     new_session = crypto.encrypt(new_session)
#
#     response = CreateCharacterResponse()
#     response.ret = 0
#     return pack_msg(response, new_session)
