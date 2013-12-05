from django.http import HttpResponse

from core.equip import generate_and_save_equip, delete_equip
from core.gem import save_gem, delete_gem
from core.character import character_change
from core.hero import save_hero


def cmd(request):
    req = request._proto
    char_id = request._char_id
    
    if req.action == 1:
        if req.tp == 1:
            character_change(char_id, exp=req.param)
        elif req.tp == 2:
            # FIXME
            print "UnSupported"
        elif req.tp == 3:
            character_change(char_id, gold=req.param)
        elif req.tp == 4:
            character_change(char_id, sycee=req.param)
        elif req.tp == 5:
            generate_and_save_equip(req.param, 1, char_id)
        elif req.tp == 6:
            save_gem([(req.param, 1)], char_id)
        elif req.tp == 7:
            save_hero(char_id, req.param)
    elif req.action == 2:
        if req.tp == 5:
            delete_equip(req.param)
        elif req.tp == 6:
            delete_gem(req.param, 1, char_id)
            
    
    return HttpResponse('', content_type='text/plain')
