
from django.http import HttpResponse

from models import Character

from core.exception import SanguoViewException
from core import notify


from core.character import char_initialize

from protomsg import CreateCharacterResponse

from utils import pack_msg
from utils import crypto



def create_character(request):
    req = request._proto

    if len(req.name) > 7:
        raise SanguoViewException(202, "CreateCharacterResponse")

    account_id, server_id = request._account_id, request._server_id

    if Character.objects.filter(account_id=account_id, server_id=server_id).exists():
        raise SanguoViewException(200, "CreateCharacterResponse")

    if Character.objects.filter(server_id=server_id,name=req.name).exists():
        raise SanguoViewException(201, "CreateCharacterResponse")

    char = char_initialize(account_id, server_id, req.name)
    
    request._char_id = char.id

    new_session = '%s:%d' % (request._session, char.id)
    new_session = crypto.encrypt(new_session)

    response = CreateCharacterResponse()
    response.ret = 0
    data = pack_msg(response, new_session)

    #notify.login_notify(
    #        request._decrypted_session,
    #        char,
    #        )
    
    notify.login_notify('noti:{0}'.format(char.id), char)

    return HttpResponse(data, content_type="text/plain")


