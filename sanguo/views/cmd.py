from django.http import HttpResponse

from core.character import Char
from core.item import Item
from core.hero import save_hero


def cmd(request):
    req = request._proto
    char_id = request._char_id

    char = Char(char_id)

    if req.action == 1:
        if req.tp == 1:
            char.update(exp=req.param, des="Cmd")
        elif req.tp == 2:
            # FIXME
            print "UnSupported"
        elif req.tp == 3:
            char.update(gold=req.param, des='Cmd')
        elif req.tp == 4:
            char.update(sycee=req.param, des='Cmd')
        elif req.tp == 5:
            item = Item(char_id)
            item.equip_add(req.param)
        elif req.tp == 6:
            item = Item(char_id)
            item.gem_add([(req.param, 1)])
        elif req.tp == 7:
            save_hero(char_id, req.param)
        elif req.tp == 8:
            item = Item(char_id)
            item.stuff_add([(req.param, 1)])
    elif req.action == 2:
        if req.tp == 5:
            item = Item(char_id)
            item.equip_remove(req.param)
        elif req.tp == 6:
            item = Item(char_id)
            item.gem_remove(req.param, 1)

    return HttpResponse('', content_type='text/plain')
