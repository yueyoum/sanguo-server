import json

from django.http import HttpResponse


from core.character import char_initialize


def character_initialize(request):
    account_id = int(request.POST['account_id'])
    server_id = int(request.POST['server_id'])
    char_id=  int(request.POST['char_id'])
    name = request.POST['name']

    ret = 0
    try:
        char_initialize(account_id, server_id, char_id, name)
    except:
        import traceback
        traceback.print_exc()
        ret = 1

    return HttpResponse(json.dumps({'ret': ret}), content_type='application/json')
