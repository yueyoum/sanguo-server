
from core.character import char_initialize, Char
from core.server import server

from utils.decorate import json_return

@json_return
def character_initialize(request):
    account_id = int(request.POST['account_id'])
    server_id = server.id
    char_id=  int(request.POST['char_id'])
    name = request.POST['name']

    ret = 0
    try:
        char_initialize(account_id, server_id, char_id, name)
    except:
        import traceback
        traceback.print_exc()
        ret = 1

    return {'ret': ret}


@json_return
def character_information(request):
    char_id = int(request.POST['char_id'])
    char = Char(char_id).mc
    return {
        'gold': char.gold,
        'sycee': char.sycee,
        'level': char.level,
        'exp': char.exp,
        'vip': char.vip,
    }

