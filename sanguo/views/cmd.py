from django.http import HttpResponse

from core.gem import save_gem, delete_gem
from core.character import Char
from core.item import Item


def cmd(request):
    req = request._proto
    char_id = request._char_id

    char = Char(char_id)

    if req.action == 1:
        if req.tp == 1:
            char.update(exp=req.param)
        elif req.tp == 2:
            # FIXME
            print "UnSupported"
        elif req.tp == 3:
            char.update(gold=req.param)
        elif req.tp == 4:
            char.update(sycee=req.param)
        elif req.tp == 5:
            item = Item(char_id)
            item.equip_add(req.param)
        elif req.tp == 6:
            save_gem([(req.param, 1)], char_id)
        elif req.tp == 7:
            char.save_hero(req.param)
    elif req.action == 2:
        if req.tp == 5:
            item = Item(char_id)
            item.equip_remove(req.param)
        elif req.tp == 6:
            delete_gem(req.param, 1, char_id)

    return HttpResponse('', content_type='text/plain')
