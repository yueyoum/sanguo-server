# -*- coding: utf-8 -*-

from core import GLOBAL
from core.mongoscheme import MongoChar
from core.exception import (
    SanguoViewException,
    InvalidOperate,
    SyceeNotEnough,
    GoldNotEnough,
    BadMessage
    )

from core.character import Char

from core.signals import (
    gem_changed_signal,
    gem_add_signal,
    gem_del_signal,
    )


def save_gem(gems, char_id):
    char = MongoChar.objects.only('gems').get(id=char_id)
    old_gems = char.gems

    gems_dict = {}
    for gid, amount in gems:
        gems_dict[gid] = gems_dict.get(gid, 0) + amount

    gems = gems_dict.items()

    new_gems = []
    update_gems = []
    for gid, amount in gems:
        gid = str(gid)
        if gid in old_gems:
            old_gems[gid] += amount

            update_gems.append((int(gid), old_gems[gid]))
        else:
            old_gems[gid] = amount
            new_gems.append((int(gid), amount))

    char.gems = old_gems
    char.save()

    if new_gems:
        gem_add_signal.send(
            sender=None,
            char_id=char_id,
            gems=new_gems
        )
    if update_gems:
        gem_changed_signal.send(
            sender=None,
            char_id=char_id,
            gems=update_gems
        )


def delete_gem(_id, _amount, char_id):
    char = MongoChar.objects.only('gems').get(id=char_id)
    this_gem_amount = char.gems[str(_id)]
    new_amount = this_gem_amount - _amount

    if new_amount < 0:
        raise Exception("delete_gem, error")
    if new_amount == 0:
        char.gems.pop(str(_id))
        char.save()
        gem_del_signal.send(
            sender=None,
            char_id=char_id,
            gid=_id
        )
    else:
        char.gems[str(_id)] = new_amount
        char.save()
        gem_changed_signal.send(
            sender=None,
            char_id=char_id,
            gems=[(_id, new_amount)]
        )


def merge_gem(_id, _amount, using_sycee, char_id):
    if _amount < 1:
        raise BadMessage("MergeGemResponse")

    condition = GLOBAL.GEM[_id]['merge_condition']
    if not condition:
        raise InvalidOperate("MergeGemResponse")

    need_buy_gem = []
    con_gid, con_amount = condition[0], 4
    char = MongoChar.objects.only('gems').get(id=char_id)
    original_amount = char.gems.get(str(con_gid), 0)
    diff_amount = original_amount - con_amount * _amount
    if diff_amount < 0:
        need_buy_gem = [con_gid, -diff_amount]
        if original_amount > 0:
            cost_gem = [con_gid, original_amount]
        else:
            cost_gem = []
    else:
        cost_gem = [con_gid, con_amount * _amount]

    c = Char(char_id)
    cache_char = c.cacheobj
    if need_buy_gem:
        if not using_sycee:
            raise SanguoViewException(600, "MergeGemResponse")
            # TODO cost
        cost = 1 * need_buy_gem[1]
        if cache_char.sycee < cost:
            raise SyceeNotEnough("MergeGemResponse")

        c.update(sycee=-cost)

    if not using_sycee:
        gold_needs = GLOBAL.GEM[_id]['level'] * _amount
        if cache_char.gold < gold_needs:
            raise GoldNotEnough("MergeGemResponse")

    if cost_gem:
        delete_gem(cost_gem[0], cost_gem[1], char_id)
    save_gem([(_id, _amount)], char_id)
