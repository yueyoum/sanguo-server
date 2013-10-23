from django.http import HttpResponse

from models import Character, CharHero

from core.exception import SanguoViewException
from core import notify

from apps.hero.models import Hero


def create_character(request):
    req = request._proto
    print req

    if len(req.name) > 7:
        raise SanguoViewException(202, req.session)

    session = req.session
    account_id, server_id = request._decrypted_session.split(':')
    account_id, server_id = int(account_id), int(server_id)

    if Character.objects.filter(account_id=account_id, server_id=server_id).exists():
        raise SanguoViewException(200, session)

    if Character.objects.filter( server_id=server_id,name=req.name).exists():
        raise SanguoViewException(201, session)


    char = Character.objects.create(
            account_id = account_id,
            server_id = server_id,
            name = req.name
            )

    init_heros = [i for i in Hero.random_items(3)]

    char_heros = []
    for hero in init_heros:
        char_heros.append(
            CharHero.objects.create(char_id=char.id, hero_id=hero.id)
            )

    notify.character_notify(request._decrypted_session, char, session)
    notify.hero_notify(request._decrypted_session, char_heros, session)
    return HttpResponse("", content_type="text/plain")


