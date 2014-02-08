# -*- coding: utf-8 -*-
import logging

from mongoengine import DoesNotExist

import protomsg
from core.counter import Counter
from core.exception import SanguoException, InvalidOperate
from core.mongoscheme import MongoHang
from core.signals import (hang_add_signal, hang_cancel_signal )
from core.stage import Stage
from core.task import Task
from worker import tasks
from utils import pack_msg, timezone
from utils.decorate import message_response

logger = logging.getLogger('sanguo')


@message_response("PVEResponse")
def pve(request):
    req = request._proto
    stage = Stage(request._char_id)
    battle_msg = stage.battle(req.stage_id)
    if battle_msg.self_win:
        drop_exp, drop_gold, drop_stuffs = stage.save_drop(req.stage_id)
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

    try:
        hang = MongoHang.objects.get(id=char_id)
    except DoesNotExist:
        hang = None

    if hang is not None:
        logger.warning("Hang. Char {0} Wanna a multi hang.".format(char_id))
        raise SanguoException(700)

    counter = Counter(char_id, 'hang')
    counter.incr(req.hours)


    # FIXME countdown
    job = tasks.hang_finish.apply_async((char_id, ), countdown=10)

    hang = MongoHang(
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
    return None

@message_response("HangCancelResponse")
def hang_cancel(request):
    req = request._proto
    char_id = request._char_id

    try:
        hang = MongoHang.objects.get(id=char_id)
    except DoesNotExist:
        logger.warning("Hang Cancel. Char {0} cancel a NONE exist hang".format(char_id))
        raise InvalidOperate()

    if hang.finished:
        logger.warning("Hang Cancel. Char {0} cancel a FINISHED hang".format(char_id))
        raise SanguoException(702)

    tasks.cancel(hang.jobid)

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
    return None

