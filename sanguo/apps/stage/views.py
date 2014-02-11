# -*- coding: utf-8 -*-

from core.stage import Stage, Hang
from core.task import Task
from utils import pack_msg
from utils.decorate import message_response

import protomsg


@message_response("PVEResponse")
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
        drop_exp, drop_gold, drop_stuffs = stage.save_drop(req.stage_id, first=stage.first, star=stage.star)
        t = Task(request._char_id)
        t.trig(1)
    else:
        drop_exp, drop_gold, drop_stuffs = 0, 0, []

    response = protomsg.PVEResponse()
    response.ret = 0
    response.stage_id = req.stage_id
    response.battle.MergeFrom(battle_msg)

    response.drop.gold = drop_gold
    response.drop.exp = drop_exp
    for _id, amount in drop_stuffs:
        stuff = response.stuffs.add()
        stuff.id = _id
        stuff.amount = amount

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

