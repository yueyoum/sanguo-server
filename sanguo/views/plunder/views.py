# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/21/14'

import logging
import random

from core.hero import Hero
from core.character import Char
from core.formation import Formation
from core.mongoscheme import MongoPlunderList
from utils import pack_msg
from utils.decorate import message_response
from core.plunder import Plunder
from core.prison import Prison
import protomsg


logger = logging.getLogger()


@message_response("PlunderListResponse")
def plunder_list(request):
    char_id = request._char_id
    p = Plunder(char_id)
    res = p.get_plunder_list()

    response = protomsg.PlunderListResponse()
    response.ret = 0

    for _id, name, gold, power, is_robot in res:
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

    p = Plunder(char_id)
    msg = p.plunder(req.id)

    if msg.self_win:
        rival_hero_oids = []

        f = Formation(req.id)
        sockets = f.formation.sockets.values()
        heros = [s.hero for s in sockets if s.hero]
        for h in heros:
            cache_hero = Hero.cache_obj(h)
            rival_hero_oids.append(cache_hero.oid)

        mongo_plunder_list = MongoPlunderList(char_id)
        drop_gold = mongo_plunder_list.chars[str(req.id)].gold

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
                prison = Prison(char_id)
                prison.prisoner_add(drop_hero_id)

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
    # FIXME
    response.drop.official_exp = 0
    if drop_hero_id:
        response.drop.heros.append(drop_hero_id)

    return pack_msg(response)

