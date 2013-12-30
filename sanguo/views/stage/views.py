# -*- coding: utf-8 -*-
import logging
import random

from django.http import HttpResponse
from mongoengine import DoesNotExist

import protomsg
from apps.character.cache import get_cache_character
from callbacks.timers import hang_job
from core import GLOBAL
from core.battle.battle import Battle
from core.battle.hero import BattleHero, MonsterHero
from core.hero.cache import get_cache_hero
from core.counter import Counter
from core.exception import SanguoViewException, InvalidOperate, CounterOverFlow, SyceeNotEnough
from core.mongoscheme import Hang, MongoChar, MongoPrison, Prisoner
from core.prison import save_prisoner
from core.signals import (hang_add_signal, hang_cancel_signal,
                          plunder_finished_signal, prisoner_add_signal,
                          pve_finished_signal, pvp_finished_signal)
from core.stage import (get_plunder_list, get_stage_fixed_drop,
                        get_stage_hang_drop, get_stage_standard_drop, save_drop)
from protomsg import Prisoner as PrisonerProtoMsg
from timer.tasks import cancel_job, sched
from utils import pack_msg, timezone

from core.character import Char
from core.prison import Prison
from preset.settings import PLUNDER_COST_SYCEE


logger = logging.getLogger('sanguo')


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


def pve(request):
    msg = protomsg.Battle()

    req = request._proto
    char_id = request._char_id

    if req.stage_id not in GLOBAL.STAGE:
        logger.warning("PVE. Char {0} pve in a NONE exist stage {1}".format(
            char_id, req.stage_id
        ))
        raise InvalidOperate("PVEResponse")

    b = PVE(char_id, req.stage_id, msg)
    b.start()

    star = False
    if msg.first_ground.self_win and msg.second_ground.self_win and msg.third_ground.self_win:
        star = True

    if msg.self_win:
        drop_exp, drop_gold, drop_equips, drop_gems = get_stage_standard_drop(char_id, req.stage_id, star)
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

    pve_finished_signal.send(
        sender=None,
        char_id=char_id,
        stage_id=req.stage_id,
        win=msg.self_win,
        star=star
    )

    response = protomsg.PVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(msg)

    response.drop.gold = drop_gold
    response.drop.exp = drop_exp
    response.drop.equips.extend([_id for _id, _l, _a in drop_equips])
    response.drop.gems.extend([_id for _id, _a in drop_gems])

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
        logger.warning("Hang. Char {0} Wanna a multi hang.".format(char_id))
        raise SanguoViewException(700, "HangResponse")

    counter = Counter(char_id, 'hang')
    counter.incr(req.hours)


    # FIXME countdown
    job = sched.apply_async((hang_job, char_id), countdown=10)

    hang = Hang(
        id=char_id,
        stage_id=req.stage_id,
        hours=req.hours,
        start=timezone.utc_timestamp(),
        finished=False,
        jobid=job.id,
        actual_hours=0,
    )

    hang.save()

    hang_add_signal.send(
        sender=None,
        char_id=char_id,
        hours=req.hours
    )

    logger.debug("Hang. Char {0} start hang with {1} hours at stage {2}".format(
        char_id, req.hours, req.stage_id
    ))

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
        logger.warning("Hang Cancel. Char {0} cancel a NONE exist hang".format(char_id))
        raise InvalidOperate("HangCancelResponse")

    if hang.finished:
        logger.warning("Hang Cancel. Char {0} cancel a FINISHED hang".format(char_id))
        raise SanguoViewException(702, "HangCancelResponse")

    cancel_job(hang.jobid)

    utc_now_timestamp = timezone.utc_timestamp()

    original_h = hang.hours
    h, s = divmod((utc_now_timestamp - hang.start), 3600)
    actual_hours = h
    if s:
        h += 1

    logger.info("Hang Cancel. Char {0} cancel a hang. Origial hour: {0}, Acutal hour: {1}".format(
        char_id, original_h, h
    ))

    counter = Counter(char_id, 'hang')
    counter.incr(-(original_h - h))

    hang_cancel_signal.send(
        sender=None,
        char_id=char_id,
        actual_hours=actual_hours
    )

    response = protomsg.HangCancelResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def plunder_list(request):
    char_id = request._char_id
    res = get_plunder_list(char_id)
    # XXX just for test
    if not res:
        from apps.character.models import Character

        ids = Character.objects.order_by('-id').values_list('id', flat=True)
        ids = ids[:10]
        res = [(i, 8) for i in ids if i != char_id]
        # END test


    response = protomsg.PlunderListResponse()
    response.ret = 0

    for _id, gold in res:
        plunder = response.plunders.add()
        plunder.id = _id

        cache_char = get_cache_character(_id)
        plunder.name = cache_char.name
        plunder.gold = gold
        c = Char(_id)
        plunder.power = c.power

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def plunder(request):
    msg = protomsg.Battle()

    req = request._proto
    char_id = request._char_id

    counter = Counter(char_id, 'plunder')
    try:
        counter.incr()
    except CounterOverFlow:
        # 使用元宝
        c = Char(char_id)
        cache_char = c.cacheobj
        if cache_char.sycee < PLUNDER_COST_SYCEE:
            raise SyceeNotEnough("PlunderResponse")

        c.update(sycee=-PLUNDER_COST_SYCEE)

    if get_cache_character(req.id) is None:
        logger.warning("Plunder. Char {0} plunder with a NONE exist char {1}".format(
            char_id, req.id
        ))
        raise InvalidOperate("PlunderResponse")

    try:
        Hang.objects.get(id=req.id)
    except DoesNotExist:
        logger.warning("Plunder. Char {0} plunder with {1}, but {1} not in hang status".format(
            char_id, req.id
        ))
        raise InvalidOperate("PlunderResponse")

    b = PVP(char_id, req.id, msg)
    b.start()

    plunder_crit = False
    if msg.first_ground.self_win and msg.second_ground.self_win and msg.third_ground.self_win:
        plunder_crit = True


    # TODO signal receive
    plunder_finished_signal.send(
        sender=None,
        from_char_id=char_id,
        to_char_id=req.id,
        is_npc=req.npc,
        is_crit=plunder_crit
    )

    rival_hero_oids = []
    mongo_char = MongoChar.objects.only('sockets').get(id=req.id)
    sockets = mongo_char.sockets.values()
    heros = [s.hero for s in sockets if s.hero]
    for h in heros:
        cache_hero = get_cache_hero(h)
        rival_hero_oids.append(cache_hero.oid)

    drop_gold = GLOBAL.STAGE[hang.stage]['normal_gold']
    drop_gold = int(drop_gold * 240 * hang.hours / 5)

    char = Char(char_id)
    char.update(gold=drop_gold)

    prison = Prison(char_id)
    drop_hero_id = 0
    if prison.prisoner_full():
        logger.debug("Plunder. Char {0} prison full. NOT drop hero".format(char_id))
    else:
        prob = 100
        if prob >= random.randint(1, 100):
            drop_hero_id = random.choice(rival_hero_oids)

        if drop_hero_id:
            save_prisoner(char_id, drop_hero_id)

    logger.debug("Plunder. Char {0} plunder success. Gold: {1}, Hero: {2}".format(
        char_id, drop_gold, drop_hero_id
    ))

    response = protomsg.PlunderResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.drop.gold = drop_gold
    response.drop.exp = 0
    response.drop.heros.append(drop_hero_id)

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


def pvp(request):
    req = request._proto
    char_id = request._char_id

    counter = Counter(char_id, 'pvp')
    counter.incr()

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
        sender=None,
        char_id=char_id,
        rival_id=rival_id,
        win=msg.self_win
    )

    logger.debug("PVP. Char {0} vs {1}, Win: {2}".format(
        char_id, rival_id, msg.self_win
    ))

    response = protomsg.ArenaResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.score = score

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
