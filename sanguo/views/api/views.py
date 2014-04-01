import json

from django.http import HttpResponse

from core.exception import SanguoException

from core.character import char_create, char_initialize

def character_create(request):
    account_id = int(request.POST['account_id'])
    server_id = int(request.POST['server_id'])
    name = request.POST['name']

    try:
        char_id = char_create(account_id, server_id, name)
        char_initialize(char_id)
    except SanguoException as e:
        res = {
            'ret': e.error_id,
            'msg': e.error_msg
        }
    else:
        res = {
            'ret': 0,
            'data': {
                'char_id': char_id
            }
        }

    return HttpResponse(json.dumps(res), content_type='application/json')
