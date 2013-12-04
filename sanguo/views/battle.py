from django.http import HttpResponse

from mongoengine import DoesNotExist

from core import GLOBAL
from core.battle.hero import BattleHero, MonsterHero
from core.battle.battle import Battle
from core.mongoscheme import MongoChar, Hang
from core.signals import pve_finished_signal
from core.stage import get_stage_drop
from core.exception import SanguoViewException
from core import notify

from apps.character.cache import get_cache_character

from utils import pack_msg
from utils import timezone

import protomsg

from core.drives import redis_client

class PVE(Battle):
    def load_my_heros(self):
        char_data = MongoChar.objects.get(id=self.my_id)
        socket_ids = char_data.formation
        sockets = char_data.sockets

        self.my_heros = []
        for hid in socket_ids:
            if hid == 0:
                self.my_heros.append(None)
            else:
                sock = sockets[str(hid)]
                hid = sock.hero
                if not hid:
                    self.my_heros.append(None)
                else:
                    h = BattleHero(hid)
                    self.my_heros.append(h)



    def load_rival_heros(self):
        monster_ids = GLOBAL.STAGE[self.rival_id]['monsters']
        self.rival_heros = []
        for mid in monster_ids:
            if mid == 0:
                self.rival_heros.append(None)
            else:
                h = MonsterHero(mid)
                self.rival_heros.append(h)


def pve(request):
    msg = protomsg.Battle()

    req = request._proto
    char_id = request._char_id

    b = PVE(char_id, req.stage_id, msg)
    b.start()
    
    star = False
    if msg.first_ground.self_win and msg.second_ground.self_win and msg.third_ground.self_win:
        star = True
    
    pve_finished_signal.send(
        sender = None,
        char_id = char_id,
        stage_id = req.stage_id,
        win = msg.self_win,
        star = star
    )
    
    drop_exp, drop_gold, drop_equips, drop_gems = get_stage_drop(char_id, req.stage_id)
    

    response = protomsg.PVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(msg)
    
    response.drop.gold = drop_gold
    response.drop.exp = drop_exp
    response.drop.equips.extend( [_id for _id, _l, _a in drop_equips] )
    response.drop.gems.extend( [_id for _id, _a in drop_gems] )

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')



def hang(request):
    req = request._proto
    char_id = request._char_id
    
    mongo_char = MongoChar.objects.only('hang_hours').get(id=char_id)
    # FIXME
    hang_hours = mongo_char.hang_hours or 8
    if req.hours > hang_hours:
        raise SanguoViewException(701, "HangResponse")
    
    try:
        hang = Hang.objects.get(id=char_id)
    except DoesNotExist:
        hang = None
    
    if hang is not None:
        raise SanguoViewException(700, "HangResponse")
    
    hang = Hang(
        id = char_id,
        stage_id = req.stage_id,
        hours = req.hours,
        start = timezone.utc_timestamp(),
        finished = False
    )
    
    hang.save()
    
    mongo_char.hang_hours = hang_hours - req.hours
    mongo_char.save()
    
    notify.hang_notify_with_data('noti:{0}'.format(char_id), mongo_char.hang_hours, hang)
    
    response = protomsg.HangResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
    

def hang_cancel(request):
    req = request._proto
    char_id = request._char_id
    
    try:
        hang = Hang.objects.get(id=char_id)
    except DoesNotExist:
        hang = None
        
    if hang is None or hang.finished:
        raise SanguoViewException(702, "HangCancelResponse")
    
    utc_now_timestamp = timezone.utc_timestamp()
    
    original_h = hang.hours
    h, s = divmod((utc_now_timestamp - hang.start), 3600)
    if s:
        h += 1
    print 'original_h =', original_h, 'h =', h
    
    mongo_char = MongoChar.objects.only('hang_hours').get(id=char_id)
    mongo_char.hang_hours += original_h - h
    
    mongo_char.save()
    
    hang.finished = True
    hang.save()
    
    # TODO send prize notify
    pn = protomsg.PrizeNotify()
    pn.prize_ids.append(1)
    
    redis_client.rpush(
        'noti:{0}'.format(char_id),
        pack_msg(pn)
    )
    
    
    
    response = protomsg.HangCancelResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')

