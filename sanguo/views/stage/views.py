# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'

from core.stage import Stage, Hang, EliteStage
from libs import pack_msg
from utils.decorate import message_response, operate_guard

import protomsg


@message_response("ElitePVEResponse")
@operate_guard('elite_pve', 15, keep_result=False)
def elite_pve(request):
    req = request._proto
    stage = EliteStage(request._char_id)

    battle_msg = stage.battle(req.stage_id)
    if battle_msg.self_win:
        drop_exp, drop_gold, drop_equipment, drop_gems, drop_stuffs = stage.save_drop()
    else:
        drop_exp, drop_gold, drop_equipment, drop_gems, drop_stuffs = 0, 0, [], [], []

    print "Elite PVE. drop:"
    print drop_exp, drop_gold, drop_equipment, drop_gems, drop_stuffs

    response = protomsg.ElitePVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(battle_msg)

    response.drop.gold = drop_gold
    response.drop.exp = drop_exp
    for _id, amount in drop_stuffs:
        stuff = response.drop.stuffs.add()
        stuff.id = _id
        stuff.amount = amount
    for _id, amount in drop_gems:
        g = response.drop.gems.add()
        g.id = _id
        g.amount = amount
    for _id, level, step in drop_equipment:
        e = response.drop.equipments.add()
        e.id = _id
        e.level = level
        e.step = step
        e.amount = 1

    return pack_msg(response)



@message_response("PVEResponse")
@operate_guard('pve', 15, keep_result=False)
def pve(request):
    req = request._proto
    stage = Stage(request._char_id)
    battle_msg = stage.battle(req.stage_id)

    # DEBUG START
    # XXX
    import os
    from django.conf import settings
    xx = os.path.join(settings.TMP_PATH, 'battle.txt')
    with open(xx, 'w') as f:
        f.write(battle_msg.__str__())
    # DEBUG END

    if battle_msg.self_win:
        drop_exp, drop_gold, drop_equipment, drop_gems, drop_stuffs = stage.save_drop(req.stage_id, first=stage.first, star=stage.first_star)
    else:
        drop_exp, drop_gold, drop_equipment, drop_gems, drop_stuffs = 0, 0, [], [],  []

    print "PVE. drop:"
    print drop_exp, drop_gold, drop_equipment, drop_gems, drop_stuffs

    response = protomsg.PVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(battle_msg)

    response.drop.gold = drop_gold
    response.drop.exp = drop_exp
    for _id, amount in drop_stuffs:
        stuff = response.drop.stuffs.add()
        stuff.id = _id
        stuff.amount = amount
    for _id, amount in drop_gems:
        g = response.drop.gems.add()
        g.id = _id
        g.amount = amount
    for _id, level, step in drop_equipment:
        e = response.drop.equipments.add()
        e.id = _id
        e.level = level
        e.step = step
        e.amount = 1

    return pack_msg(response)


@message_response("HangResponse")
def hang_start(request):
    req = request._proto
    char_id = request._char_id

    hang = Hang(char_id)
    hang.start(req.stage_id)
    return None


@message_response("HangCancelResponse")
def hang_cancel(request):
    hang = Hang(request._char_id)
    hang.cancel()

    return None

