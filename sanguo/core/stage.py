# -*- coding: utf-8 -*-
import json

import arrow
from django.conf import settings
from mongoengine import DoesNotExist

from core.mongoscheme import MongoStage, MongoEmbededPlunderLog, MongoHang, MongoHangDoing
from core.msgpipe import publish_to_char
from core.attachment import Attachment, standard_drop_to_attachment_protomsg, make_standard_drop_from_template, get_drop
from core.achievement import Achievement
from core.exception import SanguoException
from core.battle import PVE, ElitePVE, ActivityPVE
from core.character import Char
from core.functionopen import FunctionOpen
from core.mail import Mail
from core.signals import pve_finished_signal
from core.counter import Counter, ActivityStageCount
from core.resource import Resource
from core.task import Task
from core import timer
from utils import pack_msg
from utils.decorate import operate_guard, passport
from utils.checkers import not_hang_going
from utils.api import APIFailure


from preset.settings import (
    PLUNDER_DEFENSE_SUCCESS_GOLD,
    PLUNDER_DEFENSE_FAILURE_GOLD,
    PLUNDER_DEFENSE_SUCCESS_MAX_TIMES,
    PLUNDER_DEFENSE_FAILURE_MAX_TIMES,
    HANG_RESET_MAIL_TITLE,
    HANG_RESET_MAIL_CONTENT,
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
    VIP_MAX_LEVEL,
    VIP_FUNCTION,
)


from preset import errormsg
import protomsg


STAGE_ELITE_TOTAL_RESET_COST.sort(key=lambda item: -item[0])
STAGE_ELITE_RESET_COST.sort(key=lambda item: -item[0])

HANG_MAX_SECONDS_FUNCTION = lambda vip: VIP_FUNCTION[vip].hang * 3600


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

    @passport(not_hang_going, errormsg.HANG_GOING, "Stage Battle")
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
            # 当前关卡通知
            msg = protomsg.CurrentStageNotify()
            opened_func = FunctionOpen(self.char_id).trig_by_stage_id(stage_id)
            self._msg_stage(msg.stage, stage_id, star)
            msg.funcs.extend(opened_func)
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


class Hang(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.hang = MongoHang.objects.get(id=self.char_id)
        except DoesNotExist:
            self.hang = MongoHang(id=self.char_id)
            self.hang.used = 0
            self.hang.save()

        try:
            self.hang_doing = MongoHangDoing.objects.get(id=self.char_id)
        except DoesNotExist:
            self.hang_doing = None


    def cron_job(self):
        # 由系统的定时任务触发
        # linux cronjob 每天定时执行
        self.hang.used = 0
        self.hang.save()

        if self.hang_doing:
            stage_id = self.hang_doing.stage_id
            if not self.hang_doing.finished:
                # 到结算点就终止
                self.finish(set_hang=False)
        else:
            stage_id = max_star_stage_id(self.char_id)

        self.send_notify()

        remained = self.get_hang_remained()
        if remained and stage_id:
            stage = STAGES[stage_id]
            exp = remained / 15 * stage.normal_exp
            gold = remained / 15 * stage.normal_gold * 0.5
            standard_drop = make_standard_drop_from_template()
            standard_drop['exp'] = int(exp)
            standard_drop['gold'] = int(gold)

            m = Mail(self.char_id)
            m.add(
                HANG_RESET_MAIL_TITLE,
                HANG_RESET_MAIL_CONTENT,
                arrow.utcnow().to(settings.TIME_ZONE).format('YYYY-MM-DD HH:mm:ss'),
                json.dumps(standard_drop)
            )


    def timer_notify(self, actual_seconds):
        # 由每个玩家的定时任务触发。
        # 定时任务是当时挂机时开启的，会在当时的剩余时间跑完后到达这里。
        # 因为VIP的提升导致的剩余时间增加
        # 所以这里得再次检测是否有多余的剩余时间
        if not self.hang_doing or self.hang_doing.finished:
            # cron_job可能会提前结束本次挂机，并重置可用挂机时间
            # 所以如果当notify达到时，发现挂机是 finished 就直接返回
            return

        remained = self.get_hang_remained()
        if remained <= 0:
            self.finish(actual_seconds=actual_seconds)
        else:
            # 当 notify 达到，发现还有剩余时间（目前是由VIP升级导致的）
            # 那么再开启一个新的timer，callback_data中的seconds就是本次notify的seconds+新的剩余时间
            data = {
                'char_id': self.char_id,
                'seconds': actual_seconds + remained,
            }

            key = timer.register(data, remained)
            self.hang_doing.jobid = key
            self.hang_doing.save()


    def get_hang_remained(self, char=None):
        if not char:
            char = Char(self.char_id).mc
        vip = char.vip
        max_seconds = HANG_MAX_SECONDS_FUNCTION(vip)
        remained = max_seconds - self.hang.used
        if remained > 0:
            if self.hang_doing and not self.hang_doing.finished:
                remained = remained - (arrow.utcnow().timestamp - self.hang_doing.start)

        if remained <= 0:
            remained = 0
        return remained


    def start(self, stage_id):
        if self.hang_doing:
            raise SanguoException(
                errormsg.HANG_MULTI,
                self.char_id,
                "Hang Start",
                "Hang Multi"
            )

        char = Char(self.char_id).mc
        remained_time = self.get_hang_remained(char)

        if remained_time <= 0:
            if char.vip < VIP_MAX_LEVEL:
                raise SanguoException(
                    errormsg.HANG_NO_TIME,
                    self.char_id,
                    "Hang Start",
                    "Hang No Time Available. but can increase vip. current vip: {0}. max vip: {1}".format(char.vip, VIP_MAX_LEVEL)
                )
            raise SanguoException(
                errormsg.HANG_NO_TIME_FINAL,
                self.char_id,
                "Hang Start",
                "Hang No Time Available. VIP reach max level {0}".format(VIP_MAX_LEVEL)
            )

        now = arrow.utcnow().timestamp
        data = {
            'char_id': self.char_id,
            'seconds': remained_time
        }

        try:
            key = timer.register(data, remained_time)
        except APIFailure:
            raise SanguoException(
                errormsg.SERVER_FAULT,
                self.char_id,
                "Hang Start",
                "api failure"
            )

        hang_doing = MongoHangDoing(
            id=self.char_id,
            jobid=key,
            char_level=char.level,
            stage_id=stage_id,
            start=now,
            finished=False,
            actual_seconds=0,
            logs=[],
            plunder_win_times=0,
            plunder_lose_times=0,
        )
        hang_doing.save()
        self.hang_doing = hang_doing
        self.send_notify()


    def cancel(self):
        if not self.hang_doing:
            raise SanguoException(
                errormsg.HANG_NOT_EXIST,
                self.char_id,
                "Hang cancel",
                "Hang cancel. But no hang exist"
            )

        if self.hang_doing.finished:
            raise SanguoException(
                errormsg.HANG_ALREADY_FINISHED,
                self.char_id,
                "Hang Cancel",
                "Hang cancel. But hang already finished"
            )

        try:
            timer.unregister(self.hang_doing.jobid)
        except APIFailure:
            raise SanguoException(
                errormsg.SERVER_FAULT,
                self.char_id,
                "Hang Cancel",
                "api failure"
            )

        return self.finish(send_attachment=True)


    def finish(self, actual_seconds=None, set_hang=True, send_attachment=False):
        if not self.hang_doing:
            raise SanguoException(
                errormsg.HANG_NOT_EXIST,
                self.char_id,
                "Hang Finish",
                "Hang Finish. But no hang exist"
            )

        if not actual_seconds:
            actual_seconds = arrow.utcnow().timestamp - self.hang_doing.start

        if set_hang:
            self.hang.used += actual_seconds
            self.hang.save()

        self.hang_doing.finished = True
        self.hang_doing.actual_seconds = actual_seconds
        self.hang_doing.save()

        actual_hours = actual_seconds / 3600
        achievement = Achievement(self.char_id)
        achievement.trig(28, actual_hours)

        if send_attachment:
            return self.save_drop()

        self.send_notify()

        attachment = Attachment(self.char_id)
        attachment.save_to_prize(1)
        return None




    def plundered(self, who, self_win):
        if not self.hang_doing:
            return

        if self_win:
            if self.hang_doing.plunder_win_times >= PLUNDER_DEFENSE_SUCCESS_MAX_TIMES:
                return

            self.hang_doing.plunder_win_times += 1
            gold = PLUNDER_DEFENSE_SUCCESS_GOLD
        else:
            if self.hang_doing.plunder_lose_times >= PLUNDER_DEFENSE_FAILURE_MAX_TIMES:
                return

            self.hang_doing.plunder_lose_times += 1
            gold = -PLUNDER_DEFENSE_FAILURE_GOLD

        l = MongoEmbededPlunderLog()
        l.name = who
        l.gold = gold

        if len(self.hang_doing.logs) >= 5:
            self.hang_doing.logs.pop(0)

        self.hang_doing.logs.append(l)
        self.hang_doing.save()

        achievement = Achievement(self.char_id)
        achievement.trig(33, 1)

    def _actual_gold(self, drop_gold):
        drop_gold = drop_gold + self.hang_doing.plunder_win_times * PLUNDER_DEFENSE_SUCCESS_GOLD - self.hang_doing.plunder_lose_times * PLUNDER_DEFENSE_FAILURE_GOLD
        if drop_gold < 0:
            drop_gold = 0
        return drop_gold


    def save_drop(self):
        stage_id = self.hang_doing.stage_id
        actual_seconds = self.hang_doing.actual_seconds
        times = actual_seconds / 15

        stage = STAGES[stage_id]

        drop_exp = stage.normal_exp * times
        drop_gold = stage.normal_gold * times
        drop_gold = self._actual_gold(drop_gold)

        drop_ids = [int(i) for i in stage.normal_drop.split(',') if i.isdigit()]
        prepare_drop = get_drop(drop_ids, multi=times, gaussian=True)

        prepare_drop['exp'] += drop_exp
        prepare_drop['gold'] += drop_gold

        self.hang_doing.delete()
        self.hang_doing = None
        self.send_notify()

        prepare_drop = drop_after_stage_type(stage_id, prepare_drop)

        resource = Resource(self.char_id, "Hang Reward", "actual seconds = {0}, times = {1}".format(actual_seconds, times))
        standard_drop = resource.add(**prepare_drop)

        achievement = Achievement(self.char_id)
        achievement.trig(29, drop_exp)

        return standard_drop_to_attachment_protomsg(standard_drop)


    def send_notify(self):
        msg = protomsg.HangNotify()
        msg.remained_time = self.get_hang_remained()

        if self.hang_doing:
            msg.hang.stage_id = self.hang_doing.stage_id
            msg.hang.start_time = self.hang_doing.start
            if self.hang_doing.finished:
                msg.hang.used_time = self.hang_doing.actual_seconds
            else:
                msg.hang.used_time = arrow.utcnow().timestamp - self.hang_doing.start

            msg.hang.finished = self.hang_doing.finished

            times = msg.hang.used_time / 15
            stage = STAGES[self.hang_doing.stage_id]
            msg.hang.rewared_gold = self._actual_gold(stage.normal_gold * times)
            msg.hang.rewared_exp = stage.normal_exp * times

            for l in self.hang_doing.logs:
                msg_log = msg.logs.add()
                msg_log.attacker = l.name
                msg_log.win = l.gold > 0
                msg_log.gold = abs(l.gold)


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
            self.stage.activities = []
            self.stage.save()

        self.enable(STAGE_ELITE[STAGE_ELITE_FIRST_ID])


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

        self.send_remained_times_notify()

    @passport(not_hang_going, errormsg.HANG_GOING, "Elite Stage Battle")
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
            self.send_remained_times_notify()
            self.enable_next_elite_stage(_id)

            Task(self.char_id).trig(6)

        return battle_msg


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

        resource = Resource(self.char_id, "EliteStage Drop", "stage {0}".format(this_stage.id))
        standard_drop = resource.add(**prepare_drop)

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


    def send_remained_times_notify(self):
        msg = protomsg.EliteStageRemainedTimesNotify()
        free_counter = Counter(self.char_id, 'stage_elite')
        msg.max_free_times = free_counter.max_value
        msg.cur_free_times = free_counter.cur_value

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


    @passport(not_hang_going, errormsg.HANG_GOING, "Activate Stage Battle")
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

