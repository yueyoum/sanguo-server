from django.http import HttpResponse
from core.mongoscheme import Hang

from core.exception import SanguoViewException

from mongoengine import DoesNotExist

import protomsg

from utils import pack_msg


def prize_get(request):
    req = request._proto
    char_id = request._char_id
    
    prize_id = req.prize_id
    
    # XXX only support 1 now
    prize_id = 1
    
    try:
        hang = Hang.objects.get(id=char_id)
    except DoesNotExist:
        hang = None
        
    if hang is None or not hang.finished:
        raise SanguoViewException(703, "PrizeResponse")
    
    # FIXME , real prize
    hang.delete()
    
    response = protomsg.PrizeResponse()
    response.ret = 0
    response.prize_id = 1
    response.drop.gold = 100
    response.drop.exp = 100
    response.drop.equips.extend([1, 2])
    response.drop.gems.extend([1, 2])
    
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
