# -*- coding: utf-8 -*-
import random

from mongoengine import DoesNotExist
from apps.hero.models import Hero as ModelHero
from apps.stage.models import Stage as ModelStage, EliteStage as ModelEliteStage, ChallengeStage as ModelChallengeStage
from apps.stage.models import StageDrop
from core.mongoscheme import MongoStage, MongoTeamBattle, MongoEmbededPlunderLog, MongoHang, MongoHangRemainedTime

from utils import timezone
from utils import pack_msg
from core.msgpipe import publish_to_char
from core.attachment import Attachment
from core.achievement import Achievement
from core.task import Task

import protomsg
from protomsg import Attachment as MsgAttachment

from core.exception import InvalidOperate, SanguoException, SyceeNotEnough, StuffNotEnough
from core.battle import PVE, ElitePVE

from core.character import Char
from core.friend import Friend
from core.hero import save_hero
from core.item import Item
from core.timercheck import TimerCheckAbstractBase, timercheck

from utils.math import GAUSSIAN_TABLE

from preset.settings import (
    TEAMBATTLE_INCR_COST,
    HANG_SECONDS,
    DROP_PROB_BASE,
    PLUNDER_DEFENSE_SUCCESS_GOLD,
    PLUNDER_DEFENSE_FAILURE_GOLD,
    PLUNDER_DEFENSE_SUCCESS_MAX_TIMES,
    PLUNDER_DEFENSE_FAILURE_MAX_TIMES,
)

def _parse_drops(all_drops, drop_id):
    if not drop_id:
        return [], [], []

    ids = drop_id.split(',')
    equips = {}
    gems = {}
    stuffs = {}

    def _parse(text):
        if not text:
            return {}

        data = {}
        for t in text.split(','):
            _id, _prob = t.split(':')
            _id = int(_id)
            _prob = int(_prob)
            data[_id] = data.get(_id, 0) + _prob
        return data

    for _id in ids:
        int_id = int(_id)
        if int_id == 0:
            continue
        this_drop = all_drops[int_id]
        drop_equip = _parse(this_drop.equips)
        for k, v in drop_equip.iteritems():
            equips[k] = equips.get(k, 0) + v

        drop_gems = _parse(this_drop.gems)
        for k, v in drop_gems.iteritems():
            gems[k] = gems.get(k, 0) + v

        drop_stuffs = _parse(this_drop.stuffs)
        for k, v in drop_stuffs.iteritems():
            stuffs[k] = stuffs.get(k, 0) + v

    return equips.items(), gems.items(), stuffs.items()


def _make(drops):
    res = []
    for _id, prob in drops:
        a, b = divmod(prob, DROP_PROB_BASE)
        a = int(a)
        if b >= random.randint(0, DROP_PROB_BASE):
            a += 1
        if a:
            res.append((_id, a))
    return res





class Stage(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.stage = MongoStage.objects.get(id=self.char_id)
        except DoesNotExist:
            self.stage = MongoStage(id=self.char_id)
            self.stage.stages = {}
            self.stage.max_star_stage = 0
            self.stage.stage_new = 1
            self.stage.elites = {}
            self.stage.save()

        self.first = False
        self.first_star = False


    def battle(self, stage_id):
        all_stages = ModelStage.all()
        try:
            this_stage = all_stages[stage_id]
        except KeyError:
            raise InvalidOperate("PVE: Char {0} Try PVE in a NONE exist stage {1}".format(
                self.char_id, stage_id
            ))

        char = Char(self.char_id)
        char_level = char.cacheobj.level
        if char_level < this_stage.level_limit:
            raise SanguoException(1100, "PVE. Char {0} level little than level limit. {1} < {2}".format(
                self.char_id, char_level, this_stage.level_limit
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
            if str(stage_id) not in self.stage.stages:
                self.first_star = True

            if stage_id > self.stage.max_star_stage:
                self.stage.max_star_stage = stage_id

        self.star = star


        achievement = Achievement(self.char_id)

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
            stage_new = getattr(this_stage, 'next', None)
            if stage_new:
                if str(stage_new) not in self.stage.stages:
                    if self.stage.stage_new != stage_new:
                        self.stage.stage_new = stage_new

                        self.send_new_stage_notify()


            # 开启精英关卡
            elite = EliteStage(self.char_id)
            elite.enable_by_condition_id(stage_id)

            achievement.trig(7, stage_id)
            if star:
                achievement.trig(9, 1)

            t = Task(self.char_id)
            t.trig(1)
        else:
            achievement.trig(8, 1)

        self.stage.save()
        return battle_msg


    def get_drop(self, stage_id, times=1, first=False, star=False):
        """
        @param stage_id: stage id
        @type stage_id: int
        @return : exp, gold, equipment, gems, stuffs. (0, 0, [], [], [(id, amount), (id, amount)])
        @rtype: (int, int, list, list, list)
        """
        all_drops = StageDrop.all()

        this_stage = ModelStage.all()[stage_id]
        exp = this_stage.normal_exp
        gold = this_stage.normal_gold
        equipments, gems, stuffs = _parse_drops(all_drops, this_stage.normal_drop)

        def _merge(base, addition):
            base_dict = dict(base)
            for a, b in addition:
                base_dict[a] = base_dict.get(a, 0) + b

            return base_dict.items()

        if first:
            exp += this_stage.first_exp
            gold += this_stage.first_gold
            f_equips, f_gems, f_stuffs = _parse_drops(all_drops, this_stage.first_drop)

            equipments = _merge(equipments, f_equips)
            gems = _merge(gems, f_gems)
            stuffs = _merge(stuffs, f_stuffs)

        if star:
            exp += this_stage.star_exp
            gold += this_stage.star_gold
            s_equips, s_gems, s_stuffs = _parse_drops(all_drops, this_stage.star_drop)

            equipments = _merge(equipments, s_equips)
            gems = _merge(gems, s_gems)
            stuffs = _merge(stuffs, s_stuffs)

        def _multi(drops):
            for index, d in enumerate(drops):
                prob = d[1]
                new_prob = times * prob
                drops[index] = [d[0], new_prob]

        _multi(equipments)
        _multi(gems)
        _multi(stuffs)

        drop_equipments = _make(equipments)
        drop_gems = _make(gems)
        drop_stuffs = _make(stuffs)

        return exp, gold, drop_equipments, drop_gems, drop_stuffs


    def save_drop(self, stage_id, times=1, first=False, star=False, only_items=False):
        exp, gold, equipments, gems, stuffs = self.get_drop(stage_id, times=times, first=first, star=star)

        if only_items:
            exp = 0
            gold = 0

        transformed_equipments = []
        for _id, amount in equipments:
            for i in range(amount):
                transformed_equipments.append((_id, 1, 1))

        attach = Attachment(self.char_id)
        attach.save_to_char(exp=exp, gold=gold, equipments=transformed_equipments, gems=gems, stuffs=stuffs)

        return exp, gold, transformed_equipments, gems, stuffs



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



class Hang(TimerCheckAbstractBase):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.hang = MongoHang.objects.get(id=self.char_id)
        except DoesNotExist:
            self.hang = None

        try:
            self.hang_remained = MongoHangRemainedTime.objects.get(id=self.char_id)
        except DoesNotExist:
            self.hang_remained = MongoHangRemainedTime(id=self.char_id)

            if self.hang:
                self.hang_remained.crossed = True
                self.hang_remained.remained = self.hang.remained
            else:
                self.hang_remained.crossed = False
                self.hang_remained.remained = HANG_SECONDS
            self.hang_remained.save()


    def check(self):
        if not self.hang or self.hang.finished:
            return

        if timezone.utc_timestamp() - self.hang.start >= self.hang_remained.remained:
            # finish
            self.finish(actual_seconds=self.hang_remained.remained)


    def start(self, stage_id):
        if self.hang:
            raise SanguoException(700, "Hang Start: Char {0} Try to a Multi hang".format(self.char_id))

        if self.hang_remained.crossed:
            if self.hang_remained.remained <= 0:
                self.hang_remained.crossed = False
                self.hang_remained.remained = HANG_SECONDS
                self.hang_remained.save()
        else:
            if self.hang_remained.remained <= 0:
                raise InvalidOperate("Hang Start: Char {0} try to hang, But NO times available".format(self.char_id))

        # job = tasks.hang_finish.apply_async((self.char_id, remained_seconds), countdown=remained_seconds)

        char = Char(self.char_id)
        char_level = char.cacheobj.level

        hang = MongoHang(
            id=self.char_id,
            char_level=char_level,
            stage_id=stage_id,
            start=timezone.utc_timestamp(),
            finished=False,
            remained=self.hang_remained.remained,
            actual_seconds=0,
            logs=[],
            plunder_win_times=0,
            plunder_lose_times=0,
        )
        hang.save()
        self.hang = hang
        self.send_notify()


    def cancel(self):
        if not self.hang:
            raise InvalidOperate("Hang Cancel: Char {0}, NO hang to cancel".format(self.char_id))

        if self.hang.finished:
            raise InvalidOperate("Hang Cancel: Char {0} Try to cancel a finished hang".format(self.char_id))

        # tasks.cancel(self.hang.jobid)
        self.finish()


    def finish(self, actual_seconds=None):
        if not self.hang:
            raise InvalidOperate("Hang Finish: Char {0}, NO hang to finish".format(self.char_id))

        if not actual_seconds:
            actual_seconds = timezone.utc_timestamp() - self.hang.start

        remained_seconds = self.hang_remained.remained - actual_seconds
        if remained_seconds <= 0:
            remained_seconds = 0

        self.hang_remained.remained = remained_seconds
        self.hang_remained.save()

        self.hang.finished = True
        self.hang.actual_seconds = actual_seconds
        self.hang.remained = remained_seconds
        self.hang.save()

        self.send_notify()

        attachment = Attachment(self.char_id)
        attachment.save_to_prize(1)

        actual_hours = actual_seconds / 3600
        achievement = Achievement(self.char_id)
        achievement.trig(28, actual_hours)


    def plundered(self, who, self_win):
        if not self.hang:
            return

        if self_win:
            if self.hang.plunder_win_times >= PLUNDER_DEFENSE_SUCCESS_MAX_TIMES:
                return

            self.hang.plunder_win_times += 1
            gold = PLUNDER_DEFENSE_SUCCESS_GOLD
        else:
            if self.hang.plunder_lose_times >= PLUNDER_DEFENSE_FAILURE_MAX_TIMES:
                return

            self.hang.plunder_lose_times += 1
            gold = -PLUNDER_DEFENSE_FAILURE_GOLD


        l = MongoEmbededPlunderLog()
        l.name = who
        l.gold = gold

        if len(self.hang.logs) >= 5:
            self.hang.logs.pop(0)

        self.hang.logs.append(l)
        self.hang.save()

        achievement = Achievement(self.char_id)
        achievement.trig(33, 1)

    def _actual_gold(self, drop_gold):
        drop_gold = drop_gold + self.hang.plunder_win_times * PLUNDER_DEFENSE_SUCCESS_GOLD - self.hang.plunder_lose_times * PLUNDER_DEFENSE_FAILURE_GOLD
        if drop_gold < 0:
            drop_gold = 0
        return drop_gold


    def get_drop(self):
        stage_id = self.hang.stage_id
        times = self.hang.actual_seconds / 15

        stage = ModelStage.all()[stage_id]
        drop_exp = stage.normal_exp * times
        drop_gold = stage.normal_gold * times

        drop_gold = self._actual_gold(drop_gold)

        all_drops = StageDrop.all()
        drop_equips, drop_gems, drop_stuffs = _parse_drops(all_drops, stage.normal_drop)

        def _gaussian(drops):
            for index, d in enumerate(drops):
                prob = d[1]
                new_prob = times * prob * (1 + GAUSSIAN_TABLE[round(random.uniform(0.01, 0.99), 2)] * 0.08)
                drops[index] = [d[0], new_prob]

        _gaussian(drop_equips)
        _gaussian(drop_gems)
        _gaussian(drop_stuffs)

        got_equips = _make(drop_equips)
        got_gems = _make(drop_gems)
        got_stuffs = _make(drop_stuffs)

        print "HANG, drop"
        print drop_exp, drop_gold, got_equips, got_gems, got_stuffs

        self.hang.delete()
        self.hang = None
        self.send_notify()

        c = Char(self.char_id)
        c.update(exp=drop_exp, gold=drop_gold, des='Hang Reward')
        item = Item(self.char_id)
        item.stuff_add(got_stuffs)
        item.gem_add(got_gems)
        for _id, _amount in got_equips:
            for i in range(_amount):
                item.equip_add(_id)

        msg = MsgAttachment()
        msg.gold = drop_gold
        msg.exp = drop_exp
        for _id, _amount in got_stuffs:
            s = msg.stuffs.add()
            s.id = _id
            s.amount = _amount

        for _id, _amount in got_gems:
            g = msg.gems.add()
            g.id = _id
            g.amount = _amount

        for _id, _amount in got_equips:
            e = msg.equipments.add()
            e.id = _id
            e.level = 1
            e.step = 1
            e.amount = _amount

        achievement = Achievement(self.char_id)
        achievement.trig(29, drop_exp)

        return msg

    #
    # def save_drop(self):
    #     exp, gold, stuffs = self.get_drop()
    #     a = Attachment(self.char_id)
    #     a.save_to_char(exp=exp, gold=gold, stuffs=stuffs)
    #     return exp, gold, stuffs
    #

    def send_notify(self):
        msg = protomsg.HangNotify()
        if self.hang:
            msg.hang.stage_id = self.hang.stage_id
            msg.hang.start_time = self.hang.start
            if self.hang.finished:
                msg.hang.used_time = self.hang.actual_seconds
                msg.remained_time = self.hang_remained.remained
            else:
                used_time = timezone.utc_timestamp() - self.hang.start

                msg.hang.used_time = used_time
                msg.remained_time = self.hang_remained.remained - used_time


            msg.hang.finished = self.hang.finished

            times = msg.hang.used_time / 15
            stage = ModelStage.all()[self.hang.stage_id]
            msg.hang.rewared_gold = self._actual_gold(stage.normal_gold * times)
            msg.hang.rewared_exp = stage.normal_exp * times

            for l in self.hang.logs:
                msg_log = msg.logs.add()
                msg_log.attacker = l.name
                msg_log.win = l.gold > 0
                msg_log.gold = abs(l.gold)
        else:
            msg.remained_time = self.hang_remained.remained

        publish_to_char(self.char_id, pack_msg(msg))


class EliteStage(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.stage = MongoStage.objects.get(id=self.char_id)
        except DoesNotExist:
            self.stage = MongoStage(id=self.char_id)
            self.stage.stage_new = 1
            self.stage.elites = {}
            self.stage.save()

        self.check()

    def check(self):
        condition_table = ModelEliteStage.condition_table()
        for k, v in condition_table.iteritems():
            if str(k) in self.stage.stages and str(v) not in self.stage.elites:
                self.enable(v)

    def enable_by_condition_id(self, _id):
        condition_table = ModelEliteStage.condition_table()
        if _id not in condition_table:
            return
        self.enable(condition_table[_id])


    def enable(self, _id):
        str_id = str(_id)
        if _id not in ModelEliteStage.all():
            raise InvalidOperate("EliteStage Enable. Char {0} try to enable a NONE exists elite stage {1}".format(self.char_id, _id))

        if str_id in self.stage.elites:
            return

        self.stage.elites[str_id] = 0
        self.stage.save()

        msg = protomsg.NewEliteStageNotify()
        msg.stage.id = _id
        msg.stage.current_times = 0
        publish_to_char(self.char_id, pack_msg(msg))


    def battle(self, _id):
        str_id = str(_id)

        try:
            times = self.stage.elites[str_id]
        except KeyError:
            raise InvalidOperate("EliteStage Battle. Char {0} try to battle elite stage {1}. But NOT opened".format(self.char_id, _id))

        try:
            self.this_stage = ModelEliteStage.all()[_id]
        except KeyError:
            raise InvalidOperate("EliteStage Battle. Char {0} try to battle a NONE exists elite stage {1}".format(self.char_id, _id))

        if times >= self.this_stage.times:
            raise InvalidOperate("EliteStage Battle. Char {0}. already times {1}. condition times {2}".format(
                self.char_id, times, self.this_stage.times
            ))

        battle_msg = protomsg.Battle()
        b = ElitePVE(self.char_id, _id, battle_msg)
        b.start()

        if battle_msg.self_win:
            self.stage.elites[str_id] += 1
            self.stage.save()

            msg = protomsg.UpdateEliteStageNotify()
            msg.stage.id = _id
            msg.stage.current_times = self.stage.elites[str_id]
            publish_to_char(self.char_id, pack_msg(msg))

        return battle_msg


    def get_drop(self, _id=None):
        if _id:
            this_stage = ModelEliteStage.all()[_id]
        else:
            this_stage = self.this_stage

        drop_gold = this_stage.normal_gold
        drop_exp = this_stage.normal_exp

        all_drops = StageDrop.all()
        drop_equips, drop_gems, drop_stuffs = _parse_drops(all_drops, this_stage.normal_drop)

        drop_equips = _make(drop_equips)
        drop_gems = _make(drop_gems)
        drop_stuffs = _make(drop_stuffs)

        return drop_exp, drop_gold, drop_equips, drop_gems, drop_stuffs


    def save_drop(self, _id=None):
        drop_exp, drop_gold, drop_equips, drop_gems, drop_stuffs = self.get_drop(_id=_id)

        transformed_equipments = []
        for _id, amount in drop_equips:
            for i in range(amount):
                transformed_equipments.append((_id, 1, 1))

        attach = Attachment(self.char_id)
        attach.save_to_char(exp=drop_exp, gold=drop_gold, equipments=transformed_equipments, gems=drop_gems, stuffs=drop_stuffs)

        return drop_exp, drop_gold, transformed_equipments, drop_gems, drop_stuffs



    def send_notify(self):
        msg = protomsg.EliteStageNotify()
        for _id, times in self.stage.elites.iteritems():
            s = msg.stages.add()
            s.id = int(_id)
            s.current_times = times

        publish_to_char(self.char_id, pack_msg(msg))




class TeamBattle(TimerCheckAbstractBase):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mongo_tb = MongoTeamBattle.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo_tb = None


    def check(self):
        if not self.mongo_tb or self.mongo_tb.status != 2:
            return

        if (timezone.utc_timestamp() - self.mongo_tb.start_at) * self.mongo_tb.step >= 1:
            # FINISH
            self.mongo_tb.status = 3
            self.mongo_tb.save()
            self.send_notify()

            attachment = Attachment(self.char_id)
            attachment.save_to_prize(7)

    def enter(self, _id):
        if self.mongo_tb:
            raise InvalidOperate("TeamBattle Enter. Char {0} Try to enter battle {1}. But last battle NOT complete".format(
                self.char_id, _id
            ))

        try:
            this_stage = ModelChallengeStage.all()[_id]
        except KeyError:
            raise InvalidOperate("TeamBattle Enter. Char {0} Try to enter a NONE exists battle {1}".format(_id))

        char = Char(self.char_id)
        char_level = char.cacheobj.level
        if char_level < this_stage.char_level_needs:
            raise InvalidOperate("TeamBattle Enter. Char {0} Try to enter battle {1}. But level not needs. {2}".format(
                self.char_id, _id, char_level
            ))

        need_stuff_id = this_stage.open_condition_id
        need_stuff_amount = this_stage.open_condition_amount

        item = Item(self.char_id)
        if not item.has_stuff(need_stuff_id, need_stuff_amount):
            raise StuffNotEnough("TeamBattle Enter. Char {0} Try to enter battle {1}. But stuff not enough".format(self.char_id, _id))

        item.stuff_remove(need_stuff_id, need_stuff_amount)


        boss = ModelHero.get_by_grade(this_stage.level)
        boss_id = boss.keys()[0]
        boss_power = this_stage.boss_power()


        self.mongo_tb = MongoTeamBattle(id=self.char_id)
        self.mongo_tb.battle_id = _id
        self.mongo_tb.boss_id = boss_id
        self.mongo_tb.boss_power = boss_power
        self.mongo_tb.friend_ids = []
        self.mongo_tb.self_power = char.power
        self.mongo_tb.start_at = 0
        self.mongo_tb.total_seconds = this_stage.time_limit
        self.mongo_tb.status = 1
        self.mongo_tb.save()

        self.send_notify()

    def start(self, friend_ids=None):
        if not self.mongo_tb:
            raise InvalidOperate("TeamBattle Start. Char {0} try to start battle. But NOT entered".format(self.char_id))

        if self.mongo_tb.status != 1:
            raise InvalidOperate("TeamBattle Start. Char {0} try to start a already started battle {1}. status = {2}".format(
                self.char_id, self.mongo_tb.battle_id, self.mongo_tb.status
            ))

        achievement = Achievement(self.char_id)

        friend_power = 0
        if friend_ids:
            f = Friend(self.char_id)
            for fid in friend_ids:
                if not f.is_friend(fid):
                    raise InvalidOperate("TeamBattle Start. Char {0} has no friend {1}".format(self.char_id, fid))

                c = Char(fid)
                friend_power += c.power

            achievement.trig(17, 1)

        self.mongo_tb.friend_ids.extend(friend_ids)
        self.mongo_tb.self_power += friend_power
        self.mongo_tb.start_at = timezone.utc_timestamp()
        self.mongo_tb.status = 2

        step = random.uniform(1, 1.05) * self.mongo_tb.self_power / self.mongo_tb.boss_power * 0.0033
        self.mongo_tb.step = step
        self.mongo_tb.save()

        self.send_notify()


    def incr_time(self):
        if not self.mongo_tb:
            raise InvalidOperate("TeamBattle Incr Time. Char {0} try to incr time. but no battle exists".format(self.char_id))

        if self.mongo_tb.status != 2:
            raise InvalidOperate("TeamBattle Incr Time. Char {0} try to incr time. but battle {1} status = {2}".format(
                self.char_id, self.mongo_tb.battle_id, self.mongo_tb.status
            ))

        char = Char(self.char_id)
        char_sycee = char.cacheobj.sycee
        if char_sycee < TEAMBATTLE_INCR_COST:
            raise SyceeNotEnough("TeamBattle Incr Time. Char {0} try to incr time. but sycee not enough. {1} < {2}".format(
                self.char_id, char_sycee, TEAMBATTLE_INCR_COST
            ))

        char.update(sycee=-TEAMBATTLE_INCR_COST, des='TeamBattle Incr Time')

        self.mongo_tb.total_seconds += 60
        self.mongo_tb.save()
        self.send_notify()

    def get_reward(self):
        if not self.mongo_tb:
            raise InvalidOperate("TeamBattle Get Reward. Char {0} Try to get reward. But no battle exists".format(self.char_id))

        if self.mongo_tb.status != 3:
            raise InvalidOperate("TeamBattle Get Reward. Char {0} Try to get reward. But battle {1} status = {2}".format(
                self.char_id, self.mongo_tb.battle_id, self.mongo_tb.status
            ))

        this_stage = ModelChallengeStage.all()[self.mongo_tb.battle_id]
        reward_gold = this_stage.reward_gold / (len(self.mongo_tb.friend_ids) + 1)
        reward_hero_id = self.mongo_tb.boss_id

        for fid in self.mongo_tb.friend_ids:
            c = Char(fid)
            c.update(gold=reward_gold, des='TeamBattle Reward as friend')

        c = Char(self.char_id)
        c.update(gold=reward_gold, des='TeamBattle Reward as Host')
        save_hero(self.char_id, reward_hero_id)

        self.mongo_tb.delete()
        self.mongo_tb = None
        self.send_notify()

        msg = MsgAttachment()
        msg.gold = reward_gold
        msg.heros.append(reward_hero_id)
        return msg


    def send_notify(self):
        msg = protomsg.TeamBattleNotify()
        msg.incr_time_cost = TEAMBATTLE_INCR_COST
        if self.mongo_tb:
            msg.team_battle.id = self.mongo_tb.battle_id
            msg.team_battle.boss_id = self.mongo_tb.boss_id
            msg.team_battle.boss_power = self.mongo_tb.boss_power
            msg.team_battle.self_ids.extend(self.mongo_tb.friend_ids)
            msg.team_battle.self_power = self.mongo_tb.self_power

            utc_timestamp = timezone.utc_timestamp()

            step_progress = self.mongo_tb.step
            current_progress = (utc_timestamp - self.mongo_tb.start_at) * step_progress
            if current_progress > 100:
                current_progress = 100
            msg.team_battle.step_progress = step_progress
            msg.team_battle.current_progress = current_progress

            remained_time = self.mongo_tb.total_seconds - (utc_timestamp - self.mongo_tb.start_at)
            if remained_time < 0:
                remained_time = 0
            msg.team_battle.remained_time = remained_time

            msg.team_battle.status = self.mongo_tb.status

            if self.mongo_tb.status == 3:
                this_stage = ModelChallengeStage.all()[self.mongo_tb.battle_id]
                msg.team_battle.reward.gold = this_stage.reward_gold / (len(self.mongo_tb.friend_ids) + 1)
                msg.team_battle.reward.heros.append(self.mongo_tb.boss_id)

        publish_to_char(self.char_id, pack_msg(msg))


timercheck.register(Hang)
timercheck.register(TeamBattle)
