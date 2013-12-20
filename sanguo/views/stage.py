# -*- coding: utf-8 -*-

import random
from django.http import HttpResponse

from mongoengine import DoesNotExist

from core import GLOBAL
from core.battle.hero import BattleHero, MonsterHero, NPCHero
from core.battle.battle import Battle
from core.mongoscheme import MongoChar, Hang, Prison, Prisoner
from core.counter import Counter

from core.signals import pve_finished_signal
from core.stage import (
    get_plunder_list,
    get_stage_fixed_drop,
    get_stage_standard_drop,
    get_stage_hang_drop,
    save_drop,
    )
from core.exception import SanguoViewException, CounterOverFlow


from core.signals import hang_add_signal, hang_cancel_signal, plunder_finished_signal, prisoner_add_signal, pvp_finished_signal
from core.cache import get_cache_hero

from apps.character.cache import get_cache_character

from utils import pack_msg
from utils import timezone

import protomsg
from protomsg import Prisoner as PrisonerProtoMsg


from timer.tasks import sched, cancel_job
from callbacks.timers import hang_job

from core.prison import save_prisoner

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
    
    def get_my_name(self, my_id=None):
        if my_id is None:
            my_id = self.my_id
        cache_char = get_cache_character(my_id)
        return cache_char.name
    
    
    def get_rival_name(self):
        return GLOBAL.STAGE[self.rival_id]['name']



class PVP(PVE):
    def load_rival_heros(self):
        return self.load_my_heros(my_id=self.rival_id)
    
    def get_rival_name(self):
        return self.get_my_name(my_id=self.rival_id)
        


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
    
    def get_rival_name(self):
        if self.is_npc:
            # FIXME
            return 'NPC'
        return self.get_my_name(my_id=self.rival_id)



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
    
    if msg.self_win:
        drop_exp, drop_gold, drop_equips, drop_gems = get_stage_standard_drop(req.stage_id)
        fixed_exp, fixed_gold, fixed_equips, fixed_gems = get_stage_fixed_drop(req.stage_id)
        drop_exp += fixed_exp
        drop_gold += fixed_gold
        drop_equips.extend(fixed_equips)
        drop_gems.extend(fixed_gems)
        save_drop(
            char_id,
            drop_exp,
            drop_gold,
            drop_equips,
            drop_gems
        )
    else:
        drop_gold = 0
        drop_exp = 0
        drop_equips = []
        drop_gems = []
    

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
    
    try:
        hang = Hang.objects.get(id=char_id)
    except DoesNotExist:
        hang = None
    
    if hang is not None:
        raise SanguoViewException(700, "HangResponse")
    
    counter = Counter(char_id, 'hang')
    try:
        counter.incr(req.hours)
    except CounterOverFlow:
        raise SanguoViewException(701, "HangResponse")
        
    
    # FIXME countdown
    job = sched.apply_async((hang_job, char_id), countdown=10)
    
    hang = Hang(
        id = char_id,
        stage_id = req.stage_id,
        hours = req.hours,
        start = timezone.utc_timestamp(),
        finished = False,
        jobid = job.id,
        actual_hours = 0,
    )
    
    hang.save()
    
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
    
    cancel_job(hang.jobid)

    utc_now_timestamp = timezone.utc_timestamp()
    
    original_h = hang.hours
    h, s = divmod((utc_now_timestamp - hang.start), 3600)
    actual_hours = h
    if s:
        h += 1
    print 'original_h =', original_h, 'h =', h
    
    
    counter = Counter(char_id, 'hang')
    counter.incr(-(original_h-h))
    
    hang_cancel_signal.send(
        sender = None,
        char_id = char_id,
        actual_hours = actual_hours
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
        ids = Character.objects.order_by('-id').values_list('id', flat=True)
        ids = ids[:10]
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
        save_prisoner(char_id, drop_hero_id)
    
    response = protomsg.PlunderResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.drop.gold = 0
    response.drop.exp = 0
    response.drop.heros.append(drop_hero_id)
    
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
        
        


def pvp(request):
    req = request._proto
    char_id = request._char_id
    
    # FIXME
    from apps.character.models import Character
    char_ids = Character.objects.values_list('id', flat=True)
    rival_id = random.choice(char_ids)
    

    msg = protomsg.Battle()
    b = PVP(char_id, rival_id, msg)
    b.start()
    
    # FIXME
    score = 0
    if msg.self_win:
        score = 100
    
    pvp_finished_signal.send(
        sender = None,
        char_id = char_id,
        rival_id = rival_id,
        win = msg.self_win
    )
    
    response = protomsg.ArenaResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.score = score
    
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
