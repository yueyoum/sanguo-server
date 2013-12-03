from django.http import HttpResponse

from core.equip import generate_and_save_equip, delete_equip
from core.gem import save_gem, delete_gem
from core.character import model_character_change

def cmd(request):
    req = request._proto
    print req
    
    _, _, char_id = request._decrypted_session.split(':')
    char_id = int(char_id)
    
    if req.action == 1:
        if req.tp == 1:
            model_character_change(char_id, exp=req.param)
        elif req.tp == 2:
            # FIXME
            print "UnSupported"
        elif req.tp == 3:
            model_character_change(char_id, gold=req.param)
        elif req.tp == 4:
            model_character_change(char_id, gem=req.param)
        elif req.tp == 5:
            generate_and_save_equip(req.param, 1, char_id)
        elif req.tp == 6:
            save_gem([(req.param, 1)], char_id)
    elif req.action == 2:
        if req.tp == 5:
            delete_equip(req.param)
        elif req.tp == 6:
            delete_gem(req.param, 1, char_id)
            
    
    return HttpResponse('', content_type='text/plain')
