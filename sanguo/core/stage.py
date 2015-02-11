# -*- coding: utf-8 -*-

import random

from mongoengine import DoesNotExist
from core.mongoscheme import MongoStage
from core.msgpipe import publish_to_char
from core.attachment import make_standard_drop_from_template, get_drop, merge_drop
from core.exception import SanguoException
from core.battle import PVE, ElitePVE, ActivityPVE
from core.character import Char
from core.functionopen import FunctionOpen
from core.signals import pve_finished_signal
from core.counter import Counter, ActivityStageCount
from core.resource import Resource
from core.activity import ActivityEntry
from core.task import Task
from utils import pack_msg
from utils.decorate import operate_guard
from preset.settings import (
    STAGE_ELITE_RESET_COST,
    STAGE_ELITE_TOTAL_RESET_COST,

    OPERATE_INTERVAL_PVE_ACTIVITY,
)
from preset.data import (
    STAGE_TYPE,
    STAGES,
    STAGE_ELITE,
    STAGE_ELITE_CONDITION,
    STAGE_ELITE_FIRST_ID,
    STAGE_ACTIVITY,
    STAGE_ACTIVITY_CONDITION,
    STAGE_ACTIVITY_TPS,
    VIP_FUNCTION,
    VALUE_SETTING,
)
from preset import errormsg
import protomsg


STAGE_ELITE_TOTAL_RESET_COST.sort(key=lambda item: -item[0])
STAGE_ELITE_RESET_COST.sort(key=lambda item: -item[0])



def max_star_stage_id(char_id):
    s = MongoStage.objects.get(id=char_id)
    return s.max_star_stage


def drop_after_stage_type(stage_id, drop):
    stage = STAGES[stage_id]
    if not stage.tp:
        return drop

    value = STAGE_TYPE[stage.tp].value
    if not value:
        return drop

    # XXX
    if STAGE_TYPE[stage.tp].resource == 1:
        drop['exp'] = int(drop['exp'] * (1 + value / 100.0))
        return drop

    if STAGE_TYPE[stage.tp].resource == 3:
        drop['gold'] = int(drop['gold'] * (1 + value / 100.0))
        return drop

    return drop




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
            self.stage.elites_star = {}
            self.stage.activities = []
            self.stage.save()

        self.first = False
        self.first_star = False

    def get_max_battle_id(self):
        stage_ids = [int(i) for i in self.stage.stages.keys()]
        if not stage_ids:
            return 0

        max_stage_id = max(stage_ids)
        return STAGES[max_stage_id].battle

    def get_passed_max_battle_id(self):
        stage_ids = [int(i) for i in self.stage.stages.keys()]
        stage_ids.sort(reverse=True)
        for s in stage_ids:
            if STAGES[s].battle_end:
                return STAGES[s].battle

        return 0


    def battle(self, stage_id):
        try:
            this_stage = STAGES[stage_id]
        except KeyError:
            raise SanguoException(
                errormsg.STAGE_NOT_EXIST,
                self.char_id,
                "Stage Battle",
                "Stage {0} not exist".format(stage_id)
            )

        char = Char(self.char_id)
        char_level = char.mc.level
        if char_level < this_stage.level_limit:
            raise SanguoException(
                errormsg.STAGE_LEVEL_GREATER_THAN_CHAR_LEVEL,
                self.char_id,
                "Stage Battle",
                "Stage {0} level limit {1} > char level {2}".format(stage_id, this_stage.level_limit, char_level)
            )

        open_condition = this_stage.open_condition
        if open_condition and str(open_condition) not in self.stage.stages:
            raise SanguoException(
                errormsg.STAGE_NOT_OPEN,
                self.char_id,
                "Stage Battle",
                "Stage {0} not open. condition is {1}".format(stage_id, open_condition)
            )

        if str(stage_id) not in self.stage.stages:
            self.first = True

        battle_msg = protomsg.Battle()
        b = PVE(self.char_id, stage_id, battle_msg)
        b.start()

        star = False
        if battle_msg.first_ground.self_win and battle_msg.second_ground.self_win and battle_msg.third_ground.self_win:
            star = True
            if not self.stage.stages.get(str(stage_id), False):
                self.first_star = True

            if stage_id > self.stage.max_star_stage:
                self.stage.max_star_stage = stage_id

        self.star = star

        if battle_msg.self_win:
            # 当前关卡星设置
            old_star = self.stage.stages.get(str(stage_id), False)
            if not old_star:
                self.stage.stages[str(stage_id)] = star

            # 设置新关卡
            stage_new = getattr(this_stage, 'next', None)
            if stage_new:
                if str(stage_new) not in self.stage.stages:
                    if self.stage.stage_new != stage_new:
                        self.stage.stage_new = stage_new
                        self.send_new_stage_notify()

            # 发送通知
            msg = protomsg.CurrentStageNotify()
            opened_func = FunctionOpen(self.char_id).trig_by_stage_id(stage_id)
            self._msg_stage(msg.stage, stage_id, old_star or star)
            msg.funcs.extend(opened_func)
            publish_to_char(self.char_id, pack_msg(msg))

        self.stage.save()

        if battle_msg.self_win:
            # 开启精英关卡
            elite = EliteStage(self.char_id)
            elite.enable_by_condition_id(stage_id)


        pve_finished_signal.send(
            sender=None,
            char_id=self.char_id,
            stage_id=stage_id,
            win=battle_msg.self_win,
            star=star,
        )

        return battle_msg


    def save_drop(self, stage_id, first=False, star=False):
        this_stage = STAGES[stage_id]

        drop_ids = []
        if this_stage.normal_drop:
            drop_ids.extend([int(i) for i in this_stage.normal_drop.split(',')])
        if first and this_stage.first_drop:
            drop_ids.extend([int(i) for i in this_stage.first_drop.split(',')])
        if star and this_stage.star_drop:
            drop_ids.extend([int(i) for i in this_stage.star_drop.split(',')])

        perpare_drop = get_drop(drop_ids)
        perpare_drop['gold'] += this_stage.normal_exp
        perpare_drop['exp'] += this_stage.normal_gold

        if first:
            perpare_drop['gold'] += this_stage.first_gold
            perpare_drop['exp'] += this_stage.first_exp
        if star:
            perpare_drop['gold'] += this_stage.star_gold
            perpare_drop['exp'] += this_stage.star_exp

        perpare_drop = drop_after_stage_type(stage_id, perpare_drop)

        resource = Resource(self.char_id, "Stage Drop", "stage {0}".format(stage_id))
        standard_drop = resource.add(**perpare_drop)

        return standard_drop


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


class EliteStage(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.stage = MongoStage.objects.get(id=self.char_id)
        except DoesNotExist:
            self.stage = MongoStage(id=self.char_id)
            self.stage.stage_new = 1
            self.stage.elites = {}
            self.stage.elites_star = {}
            self.stage.elites_buy = {}
            self.stage.elites_times = 0
            self.stage.activities = []
            self.stage.save()

        self.enable(STAGE_ELITE[STAGE_ELITE_FIRST_ID])

        self.is_circle_reward = False


    def enable_by_condition_id(self, stage_id):
        if stage_id not in STAGE_ELITE_CONDITION:
            return

        self.enable(STAGE_ELITE_CONDITION[stage_id][0])

    def enable_next_elite_stage(self, _id):
        s = STAGE_ELITE[_id]
        if not s.next:
            return

        self.enable(STAGE_ELITE[s.next])


    def enable(self, s):
        _id = s.id
        str_id = str(_id)
        if _id not in STAGE_ELITE:
            raise SanguoException(
                errormsg.STAGE_ELITE_NOT_EXIST,
                self.char_id,
                "EliteStage Enable",
                "EliteStage {0} not exist".format(_id)
            )

        if str_id in self.stage.elites:
            return

        if str(s.open_condition) not in self.stage.stages:
            return

        if s.previous and str(s.previous) not in self.stage.elites:
            return

        self.stage.elites[str_id] = 0
        self.stage.save()
        self.send_new_notify(_id)


    def get_reset_cost(self, _id):
        buy_times = self.stage.elites_buy.get(str(_id), 0)
        buy_times += 1
        for t, cost in STAGE_ELITE_RESET_COST:
            if buy_times >= t:
                return cost

        return 0

    def get_total_reset_cost(self):
        counter = Counter(self.char_id, 'stage_elite_buy_total')
        buy_times = counter.cur_value
        buy_times += 1
        for t, cost in STAGE_ELITE_TOTAL_RESET_COST:
            if buy_times >= t:
                return cost

        return 0


    def reset_one(self, _id):
        str_id = str(_id)
        if str_id not in self.stage.elites:
            raise SanguoException(
                errormsg.STAGE_ELITE_NOT_OPEN,
                self.char_id,
                "Elite Reset One",
                "reset a not opened stage {0}".format(_id)
            )

        reset_times = self.stage.elites_buy.get(str(_id), 0)
        char = Char(self.char_id).mc
        can_reset_times = VIP_FUNCTION[char.vip].stage_elite_buy
        if reset_times >= can_reset_times:
            raise SanguoException(
                errormsg.STAGE_ELITE_RESET_FULL,
                self.char_id,
                "Elite Reset One",
                "reset {0}".format(_id)
            )

        cost = self.get_reset_cost(_id)

        resource = Resource(self.char_id, "Elite Reset One", "reset {0}".format(_id))
        with resource.check(sycee=-cost):
            self.stage.elites[str(_id)] = 0
            self.stage.elites_buy[str(_id)] = reset_times + 1
            self.stage.save()

        self.send_update_notify(_id)


    def reset_total(self):
        counter_buy = Counter(self.char_id, 'stage_elite_buy_total')
        if counter_buy.remained_value <= 0:
            raise SanguoException(
                errormsg.STAGE_ELITE_RESET_TOTAL_FULL,
                self.char_id,
                "Elite Reset Total",
                "reset total"
            )

        cost = self.get_total_reset_cost()

        resource = Resource(self.char_id, "Elite Reset Total", "")
        with resource.check(sycee=-cost):
            counter_buy.incr()
            counter = Counter(self.char_id, 'stage_elite')
            counter.reset()

        self.send_times_notify()

    # @passport(not_hang_going, errormsg.HANG_GOING, "Elite Stage Battle")
    def battle(self, _id):
        str_id = str(_id)

        try:
            self.this_stage = STAGE_ELITE[_id]
        except KeyError:
            raise SanguoException(
                errormsg.STAGE_ELITE_NOT_EXIST,
                self.char_id,
                "StageElite Battle",
                "StageElite {0} not exist".format(_id)
            )

        try:
            times = self.stage.elites[str_id]
        except KeyError:
            raise SanguoException(
                errormsg.STAGE_ELITE_NOT_OPEN,
                self.char_id,
                "StageElite Battle",
                "StageElite {0} not open".format(_id)
            )

        if str(self.this_stage.open_condition) not in self.stage.stages:
            if self.this_stage.previous and str(self.this_stage.previous) not in self.stage.elites:
                raise SanguoException(
                    errormsg.STAGE_ELITE_NOT_OPEN,
                    self.char_id,
                    "StageElite Battle",
                    "StageElite {0} not open. XXX check source core/stage/EliteStage Open".format(_id)
                )

        if times >= self.this_stage.times:
            raise SanguoException(
                errormsg.STAGE_ELITE_NO_TIMES,
                self.char_id,
                "StageElite Battle",
                "StageElite {0} no times".format(_id)
            )

        counter = Counter(self.char_id, 'stage_elite')
        if counter.remained_value <= 0:
            raise SanguoException(
                errormsg.STAGE_ELITE_TOTAL_NO_TIMES,
                self.char_id,
                "StageElite Battle",
                "stageElite no total times."
            )

        battle_msg = protomsg.Battle()
        b = ElitePVE(self.char_id, _id, battle_msg)
        b.start()

        star = False
        if battle_msg.first_ground.self_win and battle_msg.second_ground.self_win and battle_msg.third_ground.self_win:
            star = True

        if not self.stage.elites_star.get(str_id, False):
            self.stage.elites_star[str_id] = star

        self.stage.save()

        if battle_msg.self_win:
            self.stage.elites[str_id] += 1
            if self.this_stage.next:

                if str(self.this_stage.next) not in self.stage.elites:
                    self.stage.elites[str(self.this_stage.next)] = 0
                    self.send_new_notify(self.this_stage.next)
            self.stage.save()

            self.send_update_notify(_id)

            counter.incr()

            self.set_circle_times()

            self.send_times_notify()
            self.enable_next_elite_stage(_id)

            Task(self.char_id).trig(6)

        return battle_msg


    def set_circle_times(self):
        self.stage.elites_times += 1
        if self.stage.elites_times >= VALUE_SETTING['plunder_circle_times'].value + 1:
            self.stage.elites_times = 0
            self.is_circle_reward = True

        self.stage.save()

    def save_drop(self, _id=None):
        if _id:
            this_stage = STAGE_ELITE[_id]
        else:
            this_stage = self.this_stage

        exp = this_stage.normal_exp
        gold = this_stage.normal_gold

        drop_ids = [int(i) for i in this_stage.normal_drop.split(',') if i.isdigit()]

        prepare_drop = get_drop(drop_ids)
        prepare_drop['gold'] += gold
        prepare_drop['exp'] += exp

        if self.is_circle_reward:
            drop_hero_ids = this_stage.drop_hero_ids
            if drop_hero_ids:
                _drop_id = random.choice([int(i) for i in drop_hero_ids.split(',')])
                prepare_drop['heros'].append((_drop_id, 1))

        additional_drop = ActivityEntry(11001).get_additional_drop()
        drop = merge_drop([prepare_drop, additional_drop])

        resource = Resource(self.char_id, "EliteStage Drop", "stage {0}".format(this_stage.id))
        standard_drop = resource.add(**drop)

        return standard_drop


    def send_new_notify(self, _id):
        msg = protomsg.NewEliteStageNotify()
        self._msg_one_stage(msg.stage, _id)
        publish_to_char(self.char_id, pack_msg(msg))


    def send_update_notify(self, _id):
        msg = protomsg.UpdateEliteStageNotify()
        self._msg_one_stage(msg.stage, _id)
        publish_to_char(self.char_id, pack_msg(msg))


    def send_notify(self):
        msg = protomsg.EliteStageNotify()
        for _id in self.stage.elites.keys():
            s = msg.stages.add()
            self._msg_one_stage(s, int(_id))

        publish_to_char(self.char_id, pack_msg(msg))


    def send_times_notify(self):
        msg = protomsg.EliteStageTimesNotify()
        free_counter = Counter(self.char_id, 'stage_elite')
        msg.max_free_times = free_counter.max_value
        msg.cur_free_times = free_counter.cur_value

        msg.cicle_max_times = VALUE_SETTING['plunder_circle_times'].value
        msg.cicle_current_times = self.stage.elites_times

        msg.total_reset_cost = self.get_total_reset_cost()
        publish_to_char(self.char_id, pack_msg(msg))


    def _msg_one_stage(self, msg, _id):
        msg.id = _id
        msg.current_times = self.stage.elites[str(_id)]
        msg.reset_cost = self.get_reset_cost(_id)


class ActivityStage(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.stage = MongoStage.objects.get(id=self.char_id)
        except DoesNotExist:
            self.stage = MongoStage(id=self.char_id)
            self.stage.stage_new = 1
            self.stage.elites = {}
            self.stage.elites_star = {}
            self.stage.elites_buy = {}
            self.stage.activities = []
            self.stage.save()


    def check(self, char_level=None):
        if not char_level:
            char = Char(self.char_id)
            char_level = char.mc.level

        enabled = []
        for k, v in STAGE_ACTIVITY_CONDITION.iteritems():
            if char_level >= k:
                for _v in v:
                    if _v not in self.stage.activities:
                        enabled.append(_v)

        if enabled:
            self.enable(enabled)


    def enable(self, enabled):
        self.stage.activities.extend(enabled)
        self.stage.save()

        msg = protomsg.NewActivityStageNotify()
        msg.ids.extend(enabled)
        publish_to_char(self.char_id, pack_msg(msg))


    # @passport(not_hang_going, errormsg.HANG_GOING, "Activate Stage Battle")
    @operate_guard('activate_pve', OPERATE_INTERVAL_PVE_ACTIVITY, keep_result=False, char_id_name='char_id')
    def battle(self, _id):
        try:
            self.this_stage = STAGE_ACTIVITY[_id]
        except KeyError:
            raise SanguoException(
                errormsg.STAGE_ACTIVITY_NOT_EXIST,
                self.char_id,
                "StageActivity Battle",
                "StageActivity {0} not exist".format(_id)
            )

        if _id not in self.stage.activities:
            raise SanguoException(
                errormsg.STAGE_ACTIVITY_NOT_OPEN,
                self.char_id,
                "StageActivity Battle",
                "StageActivity {0} not open".format(_id)
            )

        counter = ActivityStageCount(self.char_id)
        counter.make_func_name(self.this_stage.tp)

        if counter.remained_value <= 0:
            raise SanguoException(
                errormsg.STAGE_ACTIVITY_TOTAL_NO_TIMES,
                self.char_id,
                "StageActivity Battle",
                "StageActivity no total times. battle {0}".format(_id)
            )

        battle_msg = protomsg.Battle()
        b = ActivityPVE(self.char_id, _id, battle_msg)
        b.start()

        if battle_msg.self_win:
            counter.incr()
            self.send_remained_times_notify()

            Task(self.char_id).trig(9)

        return battle_msg


    def save_drop(self):
        if self.this_stage.tp == 1:
            prepare_drop = make_standard_drop_from_template()
            prepare_drop['gold'] = self.this_stage.normal_gold
        else:
            prepare_drop = get_drop([int(i) for i in self.this_stage.normal_drop.split(',') if i.isdigit()])

        resource = Resource(self.char_id, "ActivityStage Drop", "stage {0}".format(self.this_stage.id))
        standard_drop = resource.add(**prepare_drop)

        return standard_drop


    def send_notify(self):
        msg = protomsg.ActivityStageNotify()
        msg.ids.extend(self.stage.activities)
        publish_to_char(self.char_id, pack_msg(msg))


    def send_remained_times_notify(self):
        msg = protomsg.ActivityStageRemainedTimesNotify()

        counter = ActivityStageCount(self.char_id)
        for tp in STAGE_ACTIVITY_TPS:
            msg_time = msg.remained_times.add()
            counter.make_func_name(tp)
            msg_time.tp = tp
            msg_time.times = counter.remained_value

        publish_to_char(self.char_id, pack_msg(msg))

