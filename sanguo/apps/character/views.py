
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
    print req

    if len(req.name) > 7:
        raise SanguoViewException(202, "CreateCharacterResponse")

    account_id, server_id = request._decrypted_session.split(':')
    account_id, server_id = int(account_id), int(server_id)

    if Character.objects.filter(account_id=account_id, server_id=server_id).exists():
        raise SanguoViewException(200, "CreateCharacterResponse")

    if Character.objects.filter(server_id=server_id,name=req.name).exists():
        raise SanguoViewException(201, "CreateCharacterResponse")

    char = char_initialize(account_id, server_id, req.name)

    new_session = '%s:%d' % (request._decrypted_session, char.id)
    new_session = crypto.encrypt(new_session)

    response = CreateCharacterResponse()
    response.ret = 0
    data = pack_msg(response, new_session)

    notify.login_notify(
            request._decrypted_session,
            char,
            )

    return HttpResponse(data, content_type="text/plain")


