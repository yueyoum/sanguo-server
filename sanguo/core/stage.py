# -*- coding: utf-8 -*-
import json

from mongoengine import DoesNotExist
from core.mongoscheme import MongoStage, MongoEmbededPlunderLog, MongoHang, MongoHangDoing
from utils import timezone
from utils import pack_msg
from core.msgpipe import publish_to_char
from core.attachment import Attachment, standard_drop_to_attachment_protomsg, make_standard_drop_from_template, get_drop, save_standard_drop
from core.achievement import Achievement
from core.exception import SanguoException
from core.battle import PVE, ElitePVE, ActivityPVE
from core.character import Char
from core.timercheck import TimerCheckAbstractBase, timercheck
from core.functionopen import FunctionOpen
from core.mail import Mail
from core.signals import pve_finished_signal
from core.counter import Counter
from preset.settings import (
    DATETIME_FORMAT,
    HANG_SECONDS,
    PLUNDER_DEFENSE_SUCCESS_GOLD,
    PLUNDER_DEFENSE_FAILURE_GOLD,
    PLUNDER_DEFENSE_SUCCESS_MAX_TIMES,
    PLUNDER_DEFENSE_FAILURE_MAX_TIMES,
    HANG_RESET_MAIL_TITLE,
    HANG_RESET_MAIL_CONTENT,
)
from preset.data import STAGES, STAGE_ELITE, STAGE_ELITE_CONDITION, STAGE_ACTIVITY, STAGE_ACTIVITY_CONDITION
from preset import errormsg

import protomsg


def max_star_stage_id(char_id):
    s = MongoStage.objects.get(id=char_id)
    return s.max_star_stage

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
            self.stage.activities = []
            self.stage.save()

        self.first = False
        self.first_star = False


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


            # 开启精英关卡
            elite = EliteStage(self.char_id)
            elite.enable_by_condition_id(stage_id)

        self.stage.save()

        pve_finished_signal.send(
            sender=None,
            char_id=self.char_id,
            stage_id=stage_id,
            win=battle_msg.self_win,
            star=star,
        )

        return battle_msg


    def save_drop(self, stage_id, times=1, first=False, star=False, only_items=False):
        this_stage = STAGES[stage_id]

        drop_ids = []
        if this_stage.normal_drop:
            drop_ids.extend([int(i) for i in this_stage.normal_drop.split(',')])
        if first and this_stage.first_drop:
            drop_ids.extend([int(i) for i in this_stage.first_drop.split(',')])
        if star and this_stage.star_drop:
            drop_ids.extend([int(i) for i in this_stage.star_drop.split(',')])

        standard_drop = get_drop(drop_ids, multi=times)
        standard_drop['gold'] += this_stage.normal_exp
        standard_drop['exp'] += this_stage.normal_gold

        if first:
            standard_drop['gold'] += this_stage.first_gold
            standard_drop['exp'] += this_stage.first_exp
        if star:
            standard_drop['gold'] += this_stage.star_gold
            standard_drop['exp'] += this_stage.star_exp

        if only_items:
            standard_drop['gold'] = 0
            standard_drop['sycee'] = 0
            standard_drop['exp'] = 0
            standard_drop['official_exp'] = 0

        standard_drop = save_standard_drop(self.char_id, standard_drop, des="Stage {0} drop".format(stage_id))
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


class Hang(TimerCheckAbstractBase):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.hang = MongoHang.objects.get(id=self.char_id)
        except DoesNotExist:
            self.hang = MongoHang(id=self.char_id)
            self.hang.remained = HANG_SECONDS
            self.hang.save()

        try:
            self.hang_doing = MongoHangDoing.objects.get(id=self.char_id)
        except DoesNotExist:
            self.hang_doing = None

    def check(self):
        if not self.hang_doing or self.hang_doing.finished:
            return

        if timezone.utc_timestamp() - self.hang_doing.start >= self.hang.remained:
            # finish
            self.finish(actual_seconds=self.hang.remained)


    def cronjob(self):
        remained = self.hang.remained
        self.hang.remained = HANG_SECONDS
        self.hang.save()

        if self.hang_doing:
            stage_id = self.hang_doing.stage_id
            if not self.hang_doing.finished:
                self.hang_doing.start = timezone.utc_timestamp()
                self.hang_doing.save()
        else:
            if remained:
                stage_id = max_star_stage_id(self.char_id)
            else:
                stage_id = 0

        self.send_notify()

        if remained and stage_id:
            stage = STAGES[stage_id]
            exp = remained / 15 * stage.normal_exp
            gold = remained / 15 * stage.normal_gold * 0.5
            standard_drop = make_standard_drop_from_template()
            standard_drop['exp'] = int(exp)
            standard_drop['gold'] = int(gold)

            m = Mail(self.char_id)
            m.add(HANG_RESET_MAIL_TITLE, HANG_RESET_MAIL_CONTENT, timezone.localnow().strftime(DATETIME_FORMAT), json.dumps(standard_drop))


    def start(self, stage_id):
        if self.hang_doing:
            raise SanguoException(
                errormsg.HANG_MULTI,
                self.char_id,
                "Hang Start",
                "Hang Multi"
            )

        if self.hang.remained <= 0:
            raise SanguoException(
                errormsg.HANG_NO_TIME,
                self.char_id,
                "Hang Start",
                "Hang No Time Available"
            )

        char = Char(self.char_id)
        char_level = char.cacheobj.level

        hang_doing = MongoHangDoing(
            id=self.char_id,
            char_level=char_level,
            stage_id=stage_id,
            start=timezone.utc_timestamp(),
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

        self.finish()


    def finish(self, actual_seconds=None):
        if not self.hang_doing:
            raise SanguoException(
                errormsg.HANG_NOT_EXIST,
                self.char_id,
                "Hang Finish",
                "Hang Finish. But no hang exist"
            )

        if not actual_seconds:
            actual_seconds = timezone.utc_timestamp() - self.hang_doing.start

        remained_seconds = self.hang.remained - actual_seconds
        if remained_seconds <= 0:
            remained_seconds = 0

        self.hang.remained = remained_seconds
        self.hang.save()

        self.hang_doing.finished = True
        self.hang_doing.actual_seconds = actual_seconds
        self.hang_doing.save()

        self.send_notify()

        attachment = Attachment(self.char_id)
        attachment.save_to_prize(1)

        actual_hours = actual_seconds / 3600
        achievement = Achievement(self.char_id)
        achievement.trig(28, actual_hours)


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
        times = self.hang_doing.actual_seconds / 15

        stage = STAGES[stage_id]

        drop_exp = stage.normal_exp * times
        drop_gold = stage.normal_gold * times
        drop_gold = self._actual_gold(drop_gold)

        drop_ids = [int(i) for i in stage.normal_drop.split(',')]
        standard_drop = get_drop(drop_ids, multi=times, gaussian=True)

        standard_drop['exp'] += drop_exp
        standard_drop['gold'] += drop_gold

        print "HANG, drop"
        print standard_drop

        self.hang_doing.delete()
        self.hang_doing = None
        self.send_notify()

        standard_drop = save_standard_drop(self.char_id, standard_drop, des="Hang Reward")

        achievement = Achievement(self.char_id)
        achievement.trig(29, drop_exp)

        return standard_drop_to_attachment_protomsg(standard_drop)


    def send_notify(self):
        msg = protomsg.HangNotify()

        if self.hang_doing:
            msg.hang.stage_id = self.hang_doing.stage_id
            msg.hang.start_time = self.hang_doing.start
            if self.hang_doing.finished:
                msg.hang.used_time = self.hang_doing.actual_seconds
                msg.remained_time = self.hang.remained
            else:
                used_time = timezone.utc_timestamp() - self.hang_doing.start

                msg.hang.used_time = used_time
                msg.remained_time = self.hang.remained - used_time

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
        else:
            msg.remained_time = self.hang.remained

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
            self.stage.activities = []
            self.stage.save()

        self.check()

    def check(self):
        for k, v in STAGE_ELITE_CONDITION.iteritems():
            for _v in v:
                if str(k) in self.stage.stages and str(_v) not in self.stage.elites:
                    self.enable(_v)

    def enable_by_condition_id(self, _id):
        if _id not in STAGE_ELITE_CONDITION:
            return
        for v in STAGE_ELITE_CONDITION[_id]:
            self.enable(v)


    def enable(self, _id):
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

        self.stage.elites[str_id] = 0
        self.stage.save()

        msg = protomsg.NewEliteStageNotify()
        msg.stage.id = _id
        msg.stage.current_times = 0
        publish_to_char(self.char_id, pack_msg(msg))


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
                "stageElite no total times. battle {0}".format(_id)
            )

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

            counter.incr()
            self.send_remained_times_notify(times=counter.remained_value)

        return battle_msg


    def save_drop(self, _id=None):
        if _id:
            this_stage = STAGE_ELITE[_id]
        else:
            this_stage = self.this_stage

        exp = this_stage.normal_exp
        gold = this_stage.normal_gold

        drop_ids = [int(i) for i in this_stage.normal_drop.split(',')]

        standard_drop = get_drop(drop_ids)
        standard_drop['gold'] += gold
        standard_drop['exp'] += exp

        standard_drop = save_standard_drop(self.char_id, standard_drop, des="EliteStage {0} drop".format(this_stage.id))
        return standard_drop


    def send_notify(self):
        msg = protomsg.EliteStageNotify()
        for _id, times in self.stage.elites.iteritems():
            s = msg.stages.add()
            s.id = int(_id)
            s.current_times = times

        publish_to_char(self.char_id, pack_msg(msg))


    def send_remained_times_notify(self, times=None):
        if not times:
            c = Counter(self.char_id, 'stage_elite')
            times = c.remained_value

        msg = protomsg.EliteStageRemainedTimesNotify()
        msg.times = times
        publish_to_char(self.char_id, pack_msg(msg))



class ActivityStage(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.stage = MongoStage.objects.get(id=self.char_id)
        except DoesNotExist:
            self.stage = MongoStage(id=self.char_id)
            self.stage.stage_new = 1
            self.stage.elites = {}
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

        if self.this_stage.tp == 1:
            func_name = 'stage_active_type_one'
        else:
            func_name = 'stage_active_type_two'

        counter = Counter(self.char_id, func_name)
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
            standard_drop = make_standard_drop_from_template()
            standard_drop['gold'] = self.this_stage.normal_gold
        else:
            standard_drop = get_drop([int(i) for i in self.this_stage.normal_drop.split(',')])

        standard_drop = save_standard_drop(self.char_id, standard_drop, des="ActivityStage {0} drop".format(self.this_stage.id))
        return standard_drop


    def send_notify(self):
        msg = protomsg.ActivityStageNotify()
        msg.ids.extend(self.stage.activities)
        publish_to_char(self.char_id, pack_msg(msg))


    def send_remained_times_notify(self):
        msg = protomsg.ActivityStageRemainedTimesNotify()

        counter = Counter(self.char_id, 'stage_active_type_one')
        msg.type_one_times = counter.remained_value

        counter.func_name = 'stage_active_type_two'
        msg.type_two_times = counter.remained_value

        publish_to_char(self.char_id, pack_msg(msg))





#
#
# class TeamBattle(TimerCheckAbstractBase):
#     def __init__(self, char_id):
#         self.char_id = char_id
#         try:
#             self.mongo_tb = MongoTeamBattle.objects.get(id=char_id)
#         except DoesNotExist:
#             self.mongo_tb = None
#
#
#     def check(self):
#         if not self.mongo_tb or self.mongo_tb.status != 2:
#             return
#
#         time_diff = timezone.utc_timestamp() - self.mongo_tb.start_at
#         if time_diff >= STAGE_CHALLENGE[self.mongo_tb.battle_id].time_limit or time_diff * self.mongo_tb.step >= 1:
#             # FINISH
#             self.mongo_tb.status = 3
#             self.mongo_tb.save()
#             self.send_notify()
#
#             attachment = Attachment(self.char_id)
#             attachment.save_to_prize(7)
#
#
#     def start(self, _id, friend_ids):
#         if self.mongo_tb:
#             raise InvalidOperate("TeamBattle Start. Char {0} Try to start battle {1}. But last battle NOT complete".format(
#                 self.char_id, _id
#             ))
#
#         try:
#             this_stage = STAGE_CHALLENGE[_id]
#         except KeyError:
#             raise InvalidOperate("TeamBattle Start. Char {0} Try to start a NONE exists battle {1}".format(_id))
#
#         char = Char(self.char_id)
#         char_level = char.cacheobj.level
#         if char_level < this_stage.char_level_needs:
#             raise InvalidOperate("TeamBattle Start. Char {0} Try to start battle {1}. But level not needs. {2}".format(
#                 self.char_id, _id, char_level
#             ))
#
#         need_stuff_id = this_stage.open_condition_id
#         need_stuff_amount = this_stage.open_condition_amount
#
#         item = Item(self.char_id)
#         if not item.has_stuff(need_stuff_id, need_stuff_amount):
#             raise StuffNotEnough("TeamBattle Start. Char {0} Try to start battle {1}. But stuff not enough".format(self.char_id, _id))
#
#         choosing_bosses = []
#         for k, v in HEROS.iteritems():
#             if v.grade == this_stage.level:
#                 choosing_bosses.append(k)
#
#         boss_id = random.choice(choosing_bosses)
#
#         def _get_boss_power(p):
#             if ',' in p:
#                 a, b = p.split(',')
#                 a, b = int(a), int(b)
#                 power_range = range(a, b+1)
#                 return random.choice(power_range)
#             return int(p)
#
#         boss_power = _get_boss_power(this_stage.power_range)
#
#
#         friend_power = 0
#         if friend_ids:
#             if len(friend_ids) > this_stage.aid_limit:
#                 raise InvalidOperate("TeamBattle Start. Char {0} Friend amount > aid limit".format(self.char_id))
#
#             f = Friend(self.char_id)
#             for fid in friend_ids:
#                 if not f.is_friend(fid):
#                     raise InvalidOperate("TeamBattle Start. Char {0} has no friend {1}".format(self.char_id, fid))
#
#                 c = Char(fid)
#                 friend_power += c.power
#
#             achievement = Achievement(self.char_id)
#             achievement.trig(17, 1)
#
#         item.stuff_remove(need_stuff_id, need_stuff_amount)
#
#
#         self.mongo_tb = MongoTeamBattle(id=self.char_id)
#         self.mongo_tb.battle_id = _id
#         self.mongo_tb.boss_id = boss_id
#         self.mongo_tb.boss_power = boss_power
#         self.mongo_tb.self_power = char.power + friend_power
#         self.mongo_tb.start_at = timezone.utc_timestamp()
#         self.mongo_tb.total_seconds = this_stage.time_limit
#         self.mongo_tb.status = 2
#         self.mongo_tb.friend_ids = friend_ids
#
#         step = random.uniform(1, 1.05) * self.mongo_tb.self_power / self.mongo_tb.boss_power * (1.0 / this_stage.time_limit)
#         self.mongo_tb.step = step
#         self.mongo_tb.save()
#
#         self.send_notify()
#
#
#     def get_reward(self):
#         if not self.mongo_tb:
#             raise InvalidOperate("TeamBattle Get Reward. Char {0} Try to get reward. But no battle exists".format(self.char_id))
#
#         if self.mongo_tb.status != 3:
#             raise InvalidOperate("TeamBattle Get Reward. Char {0} Try to get reward. But battle {1} status = {2}".format(
#                 self.char_id, self.mongo_tb.battle_id, self.mongo_tb.status
#             ))
#
#         this_stage = STAGE_CHALLENGE[self.mongo_tb.battle_id]
#         # FIXME
#         reward_gold = this_stage.reward_gold
#         reward_hero_id = self.mongo_tb.boss_id
#
#         # for fid in self.mongo_tb.friend_ids:
#         #     c = Char(fid)
#         #     c.update(gold=reward_gold, des='TeamBattle Reward as friend')
#
#         c = Char(self.char_id)
#         c.update(gold=reward_gold, des='TeamBattle Reward as Host')
#         save_hero(self.char_id, reward_hero_id)
#
#         self.mongo_tb.delete()
#         self.mongo_tb = None
#         self.send_notify()
#
#         msg = MsgAttachment()
#         msg.gold = reward_gold
#         msg.heros.append(reward_hero_id)
#         return msg
#
#
#     def send_notify(self):
#         msg = protomsg.TeamBattleNotify()
#         if self.mongo_tb:
#             msg.team_battle.id = self.mongo_tb.battle_id
#             msg.team_battle.boss_id = self.mongo_tb.boss_id
#             msg.team_battle.boss_power = self.mongo_tb.boss_power
#             msg.team_battle.self_power = self.mongo_tb.self_power
#
#             msg.team_battle.start_at = self.mongo_tb.start_at
#             msg.team_battle.step_progress = self.mongo_tb.step
#
#             msg.team_battle.status = self.mongo_tb.status
#
#             if self.mongo_tb.status == 3:
#                 this_stage = STAGE_CHALLENGE[self.mongo_tb.battle_id]
#                 # FIXME
#                 msg.team_battle.reward.gold = this_stage.reward_gold
#                 msg.team_battle.reward.heros.append(self.mongo_tb.boss_id)
#
#         publish_to_char(self.char_id, pack_msg(msg))


timercheck.register(Hang)
# timercheck.register(TeamBattle)
