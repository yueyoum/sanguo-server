
from django.http import HttpResponse

from apps.character.models import Character
from core.character import char_initialize
from core.exception import SanguoViewException
from core.signals import char_created_signal, login_signal
from protomsg import CreateCharacterResponse
from utils import crypto, pack_msg

from core.character import Char


def create_character(request):
    req = request._proto

    if len(req.name) > 7:
        raise SanguoViewException(202, "CreateCharacterResponse")

    account_id, server_id = request._account_id, request._server_id

    if Character.objects.filter(account_id=account_id, server_id=server_id).exists():
        raise SanguoViewException(200, "CreateCharacterResponse")

    if Character.objects.filter(server_id=server_id,name=req.name).exists():
        raise SanguoViewException(201, "CreateCharacterResponse")

    char = Char(
        account_id = account_id,
        server_id = server_id,
        name = req.name
    )
    
    login_signal.send(
        sender = None,
        account_id = account_id,
        server_id = server_id,
        char_id = char.id
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
    data = pack_msg(response, new_session)

    return HttpResponse(data, content_type="text/plain")
