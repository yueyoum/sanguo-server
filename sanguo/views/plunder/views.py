# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/21/14'


import logging
import random

from core.hero import Hero

from apps.character.models import Character as ModelCharacter

from core.exception import SyceeNotEnough, CounterOverFlow, InvalidOperate
from core.prison import save_prisoner

from core.character import Char
from core.prison import Prison
from core.formation import Formation
from core.counter import Counter


from utils import pack_msg
from utils.decorate import message_response

from preset.settings import PLUNDER_COST_SYCEE

from core.plunder import Plunder

import protomsg

logger = logging.getLogger()


@message_response("PlunderListResponse")
def plunder_list(request):
    char_id = request._char_id
    p = Plunder(char_id)
    res = p.get_plunder_list()

    response = protomsg.PlunderListResponse()
    response.ret = 0

    for _id, name, gold, power in res:
        plunder = response.plunders.add()
        plunder.id = _id
        plunder.name = name
        plunder.gold = gold
        plunder.power = power

    return pack_msg(response)


@message_response("PlunderResponse")
def plunder(request):
    req = request._proto
    char_id = request._char_id

    if ModelCharacter.cache_obj(req.id) is None:
        logger.warning("Plunder. Char {0} plunder with a NONE exist char {1}".format(
            char_id, req.id
        ))
        raise InvalidOperate()

    counter = Counter(char_id, 'plunder')
    try:
        counter.incr()
    except CounterOverFlow:
        # 使用元宝
        c = Char(char_id)
        cache_char = c.cacheobj
        if cache_char.sycee < PLUNDER_COST_SYCEE:
            raise SyceeNotEnough()

        c.update(sycee=-PLUNDER_COST_SYCEE)

    p = Plunder(char_id)
    msg = p.plunder(req.id)

    if msg.self_win:
        rival_hero_oids = []

        f = Formation(char_id)
        sockets = f.formation.sockets.values()
        heros = [s.hero for s in sockets if s.hero]
        for h in heros:
            cache_hero = Hero.cache_obj(h)
            rival_hero_oids.append(cache_hero.oid)

        # drop_gold = GLOBAL.STAGE[hang.stage]['normal_gold']
        # drop_gold = int(drop_gold * 240 * hang.hours / 5)
        # FIXME
        drop_gold = 0

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
    else:
        drop_gold = 0
        drop_hero_id = None

    response = protomsg.PlunderResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    response.drop.gold = drop_gold
    response.drop.exp = 0
    if drop_hero_id:
        response.drop.heros.append(drop_hero_id)

    return pack_msg(response)

