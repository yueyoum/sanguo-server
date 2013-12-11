# -*- coding: utf-8 -*-

import random
from django.http import HttpResponse

from mongoengine import DoesNotExist

from core import GLOBAL
from core.battle.hero import BattleHero, MonsterHero, NPCHero
from core.battle.battle import Battle
from core.mongoscheme import MongoChar, Hang, Prison, Prisoner
from core.signals import pve_finished_signal
from core.stage import get_stage_drop, get_plunder_list
from core.exception import SanguoViewException

from core.signals import hang_add_signal, hang_cancel_signal, plunder_finished_signal, prisoner_add_signal
from core.cache import get_cache_hero

from apps.character.cache import get_cache_character

from utils import pack_msg
from utils import timezone

import protomsg
from protomsg import Prisoner as PrisonerProtoMsg

from core.drives import redis_client

class PVE(Battle):
    def load_my_heros(self, my_id=None):
        if my_id is None:
            my_id = self.my_id

        char_data = MongoChar.objects.get(id=my_id)
        socket_ids = char_data.formation
        sockets = char_data.sockets

        my_heros = []
        for hid in socket_ids:
            if hid == 0:
                my_heros.append(None)
            else:
                sock = sockets[str(hid)]
                hid = sock.hero
                if not hid:
                    my_heros.append(None)
                else:
                    h = BattleHero(hid)
                    my_heros.append(h)
        
        return my_heros



    def load_rival_heros(self):
        monster_ids = GLOBAL.STAGE[self.rival_id]['monsters']
        rival_heros = []
        for mid in monster_ids:
            if mid == 0:
                rival_heros.append(None)
            else:
                h = MonsterHero(mid)
                rival_heros.append(h)
        
        return rival_heros


class Plunder(PVE):
    def __init__(self, my_id, rival_id, msg, is_npc):
        self.is_npc = is_npc
        super(Plunder, self).__init__(my_id, rival_id, msg)
    
    def load_rival_heros(self):
        if self.is_npc:
            return self.load_npc()
        return self.load_my_heros(my_id=self.rival_id)
        
    
    def load_npc(self):
        npc = GLOBAL.NPC[self.rival_id]
        level = npc['level']
        formation = npc['formation']
        
        heros = []
        for h in formation:
            if h == 0:
                heros.append(None)
            else:
                heros.append( NPCHero(h, level) )
        
        return heros



def pve(request):
    msg = protomsg.Battle()

    req = request._proto
    char_id = request._char_id

    b = PVE(char_id, req.stage_id, msg)
    b.start()
    
    # XXX
    with open('/tmp/battle.proto', 'w') as f:
        f.write(msg.__str__())
    
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
    
    hang_add_signal.send(
        sender = None,
        char_id = char_id,
        hours = req.hours
    )
    
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

    mongo_char = MongoChar.objects.only('hang_hours').get(id=char_id)
    utc_now_timestamp = timezone.utc_timestamp()
    
    original_h = hang.hours
    h, s = divmod((utc_now_timestamp - hang.start), 3600)
    if s:
        h += 1
    print 'original_h =', original_h, 'h =', h
    
    mongo_char.hang_hours += original_h - h
    mongo_char.save()
    
    hang_cancel_signal.send(
        sender = None,
        char_id = char_id
    )
    
    response = protomsg.HangCancelResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def plunder_list(request):
    char_id = request._char_id
    res = get_plunder_list(char_id)
    print res
    # XXX just for test
    if not res:
        from apps.character.models import Character
        ids = Character.objects.all().values_list('id', flat=True)
        res = [(i, False, 8) for i in ids if i != char_id]
    # END test
    print res
        
        
    response = protomsg.PlunderListResponse()
    response.ret = 0
    
    for _id, is_npc, hours in res:
        plunder = response.plunders.add()
        plunder.id = _id
        plunder.npc = is_npc
        if is_npc:
            # TODO
            pass
        else:
            cache_char = get_cache_character(_id)
            plunder.name = cache_char.name
            # FIXME
            plunder.gold = hours
            plunder.power = 100
    
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')



def plunder(request):
    msg = protomsg.Battle()

    req = request._proto
    char_id = request._char_id

    b = Plunder(char_id, req.id, msg, req.npc)
    b.start()
    
    
    plunder_crit = False
    if msg.first_ground.self_win and msg.second_ground.self_win and msg.third_ground.self_win:
        plunder_crit = True


    # TODO signal receive
    plunder_finished_signal.send(
        sender = None,
        from_char_id = char_id,
        to_char_id = req.id,
        is_npc = req.npc,
        is_crit = plunder_crit
    )
    
    rival_hero_oids = []
    if req.npc:
        formation = GLOBAL.NPC[req.id]['formation']
        rival_hero_oids = [h for h in formation if h]
    else:
        mongo_char = MongoChar.objects.only('sockets').get(id=req.id)
        sockets = mongo_char.sockets.values()
        heros = [s.hero for s in sockets if s.hero]
        for h in heros:
            cache_hero = get_cache_hero(h)
            rival_hero_oids.append(cache_hero.oid)
    
    print 'rival_hero_oids =', rival_hero_oids
        
    # FIXME 如果战俘列表满了，就不掉落
    drop_hero_id = 0
    prob = 100
    if prob >= random.randint(1, 100):
        drop_hero_id = random.choice(rival_hero_oids)
    
    if drop_hero_id:
        prison = Prison.objects.only('prisoners').get(id=char_id)
        prisoner_ids = [int(i) for i in prison.prisoners.keys()]
        
        new_persioner_id = 1
        while True:
            if new_persioner_id not in prisoner_ids:
                break
            new_persioner_id += 1
        
        
        p = Prisoner()
        p.id = new_persioner_id
        p.oid = drop_hero_id
        p.start_time = timezone.utc_timestamp()
        p.status = PrisonerProtoMsg.NOT
        
        
        prison.prisoners[str(new_persioner_id)] = p
        prison.save()
        
        prisoner_add_signal.send(
            sender = None,
            char_id = char_id,
            mongo_prisoner_obj = p
        )
        
        
    
    response = protomsg.PlunderResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.drop.gold = 0
    response.drop.exp = 0
    response.drop.heros.append(drop_hero_id)
    
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
        
        
        
        
        
