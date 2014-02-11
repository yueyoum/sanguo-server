# -*- coding: utf-8 -*-
import random

from mongoengine import DoesNotExist
from apps.stage.models import Stage as ModelStage
from apps.stage.models import StageDrop
from core.mongoscheme import MongoStage

from utils import timezone
from utils import pack_msg
from core.msgpipe import publish_to_char
from core.world import Attachment

import protomsg

from core.exception import InvalidOperate, SanguoException
from core.battle import PVE

from core.mongoscheme import MongoHang, MongoEmbededPlunderLog
from core.counter import Counter
from core.character import Char

from worker import tasks
from utils.math import GAUSSIAN_TABLE

def _parse_drops(all_drops, drop_id):
    if not drop_id:
        return []
    ids = drop_id.split(',')
    res = []
    for _id in ids:
        drop = all_drops[int(_id)].drops
        for d in drop.split(','):
            stuff_id, prob = d.split(':')
            stuff_id = int(stuff_id)
            prob = float(prob)
            res.append((stuff_id, prob))
    return res




class Stage(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.stage = MongoStage.objects.get(id=self.char_id)
        except DoesNotExist:
            self.stage = MongoStage(id=self.char_id)
            self.stage.stage_new = 1
            self.stage.save()

        self.first = False


    def battle(self, stage_id):
        all_stages = ModelStage.all()
        try:
            this_stage = all_stages[stage_id]
        except KeyError:
            raise InvalidOperate("PVE: Char {0} Try PVE in a NONE exist stage {1}".format(
                self.char_id, stage_id
            ))

        open_condition = this_stage.open_condition
        if open_condition and str(open_condition) not in self.stage.stages:
            raise InvalidOperate("PVE: Char {0} Try PVE in stage {1}. But Open Condition Check NOT passed. {2}".format(
                self.char_id, stage_id, open_condition
            ))

        if str(stage_id) not in self.stage.stages:
            self.first = True

        battle_msg = protomsg.Battle()
        b = PVE(self.char_id, stage_id, battle_msg)
        b.start()

        star = False
        if battle_msg.first_ground.self_win and battle_msg.second_ground.self_win and battle_msg.third_ground.self_win:
            star = True

        self.star = star

        if battle_msg.self_win:
            # 当前关卡通知
            msg = protomsg.CurrentStageNotify()
            self._msg_stage(msg.stage, stage_id, star)
            publish_to_char(self.char_id, pack_msg(msg))

            if str(stage_id) not in self.stage.stages:
                self.stage.stages[str(stage_id)] = star
            else:
                if not self.stage.stages[str(stage_id)]:
                    self.stage.stages[str(stage_id)] = star

            # 设置新关卡

            stage_new = this_stage.next
            if str(stage_new) not in self.stage.stages:
                if self.stage.stage_new != stage_new:
                    self.stage.stage_new = stage_new

                    self.send_new_stage_notify()
            self.stage.save()

        return battle_msg


    def get_drop(self, stage_id, first=False, star=False):
        """
        @param stage_id: stage id
        @type stage_id: int
        @return : exp, gold, stuffs. (0, 0, [(id, amount), (id, amount)])
        @rtype: (int, int, list)
        """
        all_drops = StageDrop.all()

        this_stage = ModelStage.all()[stage_id]
        exp = this_stage.normal_exp
        gold = this_stage.normal_gold
        stuffs = _parse_drops(all_drops, this_stage.normal_drop)

        if first:
            exp += this_stage.first_exp
            gold += this_stage.first_gold
            stuffs.extend(_parse_drops(all_drops, this_stage.first_drop))

        if star:
            exp += this_stage.star_exp
            gold += this_stage.star_gold
            stuffs.extend(_parse_drops(all_drops, this_stage.star_drop))

        drop_stuffs = {}
        for _id, prob in stuffs:
            if prob >= random.uniform(0, 100):
                drop_stuffs[_id] = drop_stuffs.get(_id, 0) + 1

        return exp, gold, drop_stuffs.items()


    def save_drop(self, stage_id, first=False, star=False):
        exp, gold, stuffs = self.get_drop(stage_id, first=first, star=star)

        attach = Attachment(self.char_id)
        attach.save_raw_attachment(exp=exp, gold=gold, stuffs=stuffs)

        return exp, gold, stuffs



    def _msg_stage(self, msg, stage_id, star):
        msg.id = stage_id
        msg.star = star

    def send_new_stage_notify(self):
        msg = protomsg.NewStageNotify()
        self._msg_stage(msg.stage, self.stage.stage_new, False)
        publish_to_char(self.char_id, pack_msg(msg))

    def send_already_stage_notify(self):
        msg = protomsg.AlreadyStageNotify()
        for _id, star in self.stage.stages.iteritems():
            s = msg.stages.add()
            self._msg_stage(s, int(_id), star)

        publish_to_char(self.char_id, pack_msg(msg))



class Hang(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.hang = MongoHang.objects.get(id=self.char_id)
            if self.hang.finished:
                self.send_prize_notify()
        except DoesNotExist:
            self.hang = None

    def start(self, stage_id):
        if self.hang:
            raise SanguoException(700, "Hang Start: Char {0} Try to a Multi hang".format(self.char_id))

        counter = Counter(self.char_id, 'hang')
        remained_seconds = counter.remained_value

        if remained_seconds <= 0:
            raise InvalidOperate("Hang Start: Char {0} try to hang, But NO times available".format(self.char_id))

        job = tasks.hang_finish.apply_async((self.char_id, remained_seconds), countdown=remained_seconds)

        char = Char(self.char_id)
        char_level = char.cacheobj.level

        hang = MongoHang(
            id=self.char_id,
            char_level=char_level,
            stage_id=stage_id,
            start=timezone.utc_timestamp(),
            finished=False,
            jobid=job.id,
            actual_hours=0,
            logs=[],
            plunder_gold=0,
            plunder_time=0,
        )
        hang.save()
        self.hang = hang
        self.send_notify()


    def cancel(self):
        if not self.hang:
            raise InvalidOperate("Hang Cancel: Char {0}, NO hang to calcel".format(self.char_id))

        if self.hang.finished:
            raise InvalidOperate("Hang Cancel: Char {0} Try to cancel a finished hang".format(self.char_id))

        tasks.cancel(self.hang.jobid)
        self.finish()


    def finish(self, actual_seconds=None):
        if not self.hang:
            raise InvalidOperate("Hang Finish: Char {0}, NO hang to finish".format(self.char_id))

        if not actual_seconds:
            actual_seconds = timezone.utc_timestamp() - self.hang.start

        self.hang.finished = True
        self.hang.actual_seconds = actual_seconds
        self.hang.save()

        counter = Counter(self.char_id, 'hang')
        counter.incr(actual_seconds)

        self.send_notify()
        self.send_prize_notify()


    def plundered(self, who, win):
        if not self.hang:
            return
        now = timezone.utc_timestamp()
        if now - self.hang.plunder_time < 15:
            return

        stage = ModelStage.all()[self.hang.stage_id]
        gold = stage.normal_gold
        if not win:
            gold = -gold

        self.hang.plunder_time = now
        self.hang.plunder_gold += gold

        l = MongoEmbededPlunderLog()
        l.name = who
        l.gold = gold

        if len(self.hang.logs) >= 20:
            self.hang.logs.pop(0)

        self.hang.append(l)
        self.hang.save()



    def get_drop(self):
        stage_id = self.hang.stage_id
        times = self.hang.actual_seconds / 15

        stage = ModelStage.all()[stage_id]
        drop_exp = stage.normal_exp * times + self.hang.plunder_gold
        drop_gold = stage.normal_gold * times

        all_drops = StageDrop.all()
        drop_stuffs = _parse_drops(all_drops, stage.normal_drop)
        for index, d in enumerate(drop_stuffs):
            prob = d[1]
            new_prob = times * prob * (1 + GAUSSIAN_TABLE[round(random.uniform(0, 1), 2)] * 0.08)
            drop_stuffs[index][1] = new_prob

        stuffs = []
        for _id, prob in drop_stuffs:
            a, b = divmod(prob, 100)
            a = int(a)
            if b >= random.uniform(0, 1):
                a += 1
            stuffs.append((_id, a))

        return drop_exp, drop_gold, stuffs


    def save_drop(self):
        exp, gold, stuffs = self.get_drop()
        a = Attachment(self.char_id)
        a.save_raw_attachment(exp=exp, gold=gold, stuffs=stuffs)
        return exp, gold, stuffs


    def send_prize_notify(self):
        msg = protomsg.PrizeNotify()
        msg.prize_ids.append(1)
        publish_to_char(self.char_id, pack_msg(msg))


    def send_notify(self):
        msg = protomsg.HangNotify()
        counter = Counter(self.char_id, 'hang')
        msg.remained_time = counter.remained_value
        if self.hang:
            msg.hang.stage_id = self.hang.stage_id
            msg.hang.start_time = self.hang.start
            msg.hang.finished = self.hang.finished

            times = (timezone.utc_timestamp() - self.hang.start) / 15
            stage = ModelStage.all()[self.hang.stage_id]
            msg.hang.rewared_gold = stage.normal_gold * times + self.hang.plunder_gold

            for l in self.hang.logs:
                msg_log = msg.logs.add()
                msg_log.attacker = l.name
                msg_log.win = l.gold > 0
                msg_log.gold = abs(l.gold)

        publish_to_char(self.char_id, pack_msg(msg))


