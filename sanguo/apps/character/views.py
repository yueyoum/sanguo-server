from django.http import HttpResponse

from models import Character

from core.exception import SanguoViewException
from core import notify


def create_character(request):
    req = request._proto
    print req

    # TODO check name lenght
    session = req.session
    account_id, server_id = request._decrypted_session.split(':')
    account_id, server_id = int(account_id), int(server_id)

    if Character.objects.filter(account_id=account_id, server_id=server_id).exists():
        raise SanguoViewException(200, session)

    if Character.objects.filter(name=req.name).exists():
        raise SanguoViewException(201, session)


    char = Character.objects.create(
            account_id = account_id,
            server_id = server_id,
            name = req.name
            )

    notify.character_notify(request._decrypted_session, char, session)
    return HttpResponse("", content_type="text/plain")


