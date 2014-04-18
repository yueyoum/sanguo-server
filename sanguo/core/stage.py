# -*- coding: utf-8 -*-
import random

from mongoengine import DoesNotExist

from core.mongoscheme import MongoStage, MongoTeamBattle, MongoEmbededPlunderLog, MongoHang, MongoHangRemainedTime


from utils import timezone
from utils import pack_msg
from core.msgpipe import publish_to_char
from core.attachment import Attachment, standard_drop_to_attachment_protomsg
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
from core.functionopen import FunctionOpen
from core.signals import pve_finished_signal

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

from preset.data import HEROS, STAGES, STAGE_CHALLENGE, STAGE_ELITE, STAGE_DROP, STAGE_ELITE_CONDITION, PACKAGES


def get_drop(drop_ids, multi=1, gaussian=False):
    # 从pakcage中解析并计算掉落，返回为 dict
    # {
    #     'gold': 0,
    #     'sycee': 0,
    #     'exp': 0,
    #     'official_exp': 0,
    #     'heros': [
    #         {id: level: step: amount:},...
    #     ],
    #     'equipments': [
    #         {id: level: amount:},...
    #     ],
    #     'gems': [
    #         {id: amount:},...
    #     ],
    #     'stuffs': [
    #         {id: amount:},...
    #     ]
    # }
    gold = 0
    sycee = 0
    exp = 0
    official_exp = 0
    heros = []
    equipments = []
    gems = []
    stuffs = []
    for d in drop_ids:
        if d == 0:
            # 一般不会为0，0实在策划填写编辑器的时候本来为空，却填了个0
            continue

        p = PACKAGES[d]
        gold += p['gold']
        sycee += p['sycee']
        exp += p['exp']
        official_exp += p['official_exp']
        heros.extend(p['heros'])
        equipments.extend(p['equipments'])
        gems.extend(p['gems'])
        stuffs.extend(p['stuffs'])

    def _make(items):
        final_items = []
        for index, item in enumerate(items):
            prob = item['prob'] * multi
            if gaussian:
                prob = prob * (1 + GAUSSIAN_TABLE[round(random.uniform(0.01, 0.99), 2)] * 0.08)

            a, b = divmod(prob, DROP_PROB_BASE)
            a = int(a)
            if b > random.randint(0, DROP_PROB_BASE):
                a += 1

            if a == 0:
                continue

            item['amount'] *= a
            item.pop('prob')
            final_items.append(item)

        return final_items

    heros = _make(heros)
    equipments = _make(equipments)
    gems = _make(gems)
    stuffs = _make(stuffs)

    return {
        'gold': gold * multi,
        'sycee': sycee * multi,
        'exp': exp * multi,
        'official_exp': official_exp * multi,
        'heros': heros,
        'equipments': equipments,
        'gems': gems,
        'stuffs': stuffs,
    }




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
        try:
            this_stage = STAGES[stage_id]
        except KeyError:
            raise InvalidOperate("PVE: Char {0} Try PVE in a NONE exist stage {1}".format(
                self.char_id, stage_id
            ))

        char = Char(self.char_id)
        char_level = char.mc.level
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
        exp = this_stage.normal_exp
        gold = this_stage.normal_gold

        drop_ids = []
        if this_stage.normal_drop:
            drop_ids.extend([int(i) for i in this_stage.normal_drop.split(',')])
        if first and this_stage.first_drop:
            drop_ids.extend([int(i) for i in this_stage.first_drop.split(',')])
        if star and this_stage.star_drop:
            drop_ids.extend([int(i) for i in this_stage.star_drop.split(',')])

        standard_drop = get_drop(drop_ids, multi=times)
        standard_drop['gold'] += gold
        standard_drop['exp'] += exp

        if only_items:
            standard_drop['gold'] = 0
            standard_drop['sycee'] = 0
            standard_drop['exp'] = 0
            standard_drop['official_exp'] = 0

        attachment = Attachment(self.char_id)
        attachment.save_standard_drop(standard_drop, des='Stage, save drop')

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


    def save_drop(self):
        stage_id = self.hang.stage_id
        times = self.hang.actual_seconds / 15

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

        self.hang.delete()
        self.hang = None
        self.send_notify()

        attachment = Attachment(self.char_id)
        attachment.save_standard_drop(standard_drop, des='Hang Reward')

        achievement = Achievement(self.char_id)
        achievement.trig(29, drop_exp)

        return standard_drop_to_attachment_protomsg(standard_drop)


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
            stage = STAGES[self.hang.stage_id]
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
            self.this_stage = STAGE_ELITE[_id]
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

        attachment = Attachment(self.char_id)
        attachment.save_standard_drop(standard_drop, des='EliteStage, save drop')

        return standard_drop


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

        time_diff = timezone.utc_timestamp() - self.mongo_tb.start_at
        if time_diff >= STAGE_CHALLENGE[self.mongo_tb.battle_id].time_limit or time_diff * self.mongo_tb.step >= 1:
            # FINISH
            self.mongo_tb.status = 3
            self.mongo_tb.save()
            self.send_notify()

            attachment = Attachment(self.char_id)
            attachment.save_to_prize(7)


    def start(self, _id, friend_ids):
        if self.mongo_tb:
            raise InvalidOperate("TeamBattle Start. Char {0} Try to start battle {1}. But last battle NOT complete".format(
                self.char_id, _id
            ))

        try:
            this_stage = STAGE_CHALLENGE[_id]
        except KeyError:
            raise InvalidOperate("TeamBattle Start. Char {0} Try to start a NONE exists battle {1}".format(_id))

        char = Char(self.char_id)
        char_level = char.cacheobj.level
        if char_level < this_stage.char_level_needs:
            raise InvalidOperate("TeamBattle Start. Char {0} Try to start battle {1}. But level not needs. {2}".format(
                self.char_id, _id, char_level
            ))

        need_stuff_id = this_stage.open_condition_id
        need_stuff_amount = this_stage.open_condition_amount

        item = Item(self.char_id)
        if not item.has_stuff(need_stuff_id, need_stuff_amount):
            raise StuffNotEnough("TeamBattle Start. Char {0} Try to start battle {1}. But stuff not enough".format(self.char_id, _id))

        choosing_bosses = []
        for k, v in HEROS.iteritems():
            if v.grade == this_stage.level:
                choosing_bosses.append(k)

        boss_id = random.choice(choosing_bosses)

        def _get_boss_power(p):
            if ',' in p:
                a, b = p.split(',')
                a, b = int(a), int(b)
                power_range = range(a, b+1)
                return random.choice(power_range)
            return int(p)

        boss_power = _get_boss_power(this_stage.power_range)


        friend_power = 0
        if friend_ids:
            if len(friend_ids) > this_stage.aid_limit:
                raise InvalidOperate("TeamBattle Start. Char {0} Friend amount > aid limit".format(self.char_id))

            f = Friend(self.char_id)
            for fid in friend_ids:
                if not f.is_friend(fid):
                    raise InvalidOperate("TeamBattle Start. Char {0} has no friend {1}".format(self.char_id, fid))

                c = Char(fid)
                friend_power += c.power

            achievement = Achievement(self.char_id)
            achievement.trig(17, 1)

        item.stuff_remove(need_stuff_id, need_stuff_amount)


        self.mongo_tb = MongoTeamBattle(id=self.char_id)
        self.mongo_tb.battle_id = _id
        self.mongo_tb.boss_id = boss_id
        self.mongo_tb.boss_power = boss_power
        self.mongo_tb.self_power = char.power + friend_power
        self.mongo_tb.start_at = timezone.utc_timestamp()
        self.mongo_tb.total_seconds = this_stage.time_limit
        self.mongo_tb.status = 2
        self.mongo_tb.friend_ids = friend_ids

        step = random.uniform(1, 1.05) * self.mongo_tb.self_power / self.mongo_tb.boss_power * (1.0 / this_stage.time_limit)
        self.mongo_tb.step = step
        self.mongo_tb.save()

        self.send_notify()


    def get_reward(self):
        if not self.mongo_tb:
            raise InvalidOperate("TeamBattle Get Reward. Char {0} Try to get reward. But no battle exists".format(self.char_id))

        if self.mongo_tb.status != 3:
            raise InvalidOperate("TeamBattle Get Reward. Char {0} Try to get reward. But battle {1} status = {2}".format(
                self.char_id, self.mongo_tb.battle_id, self.mongo_tb.status
            ))

        this_stage = STAGE_CHALLENGE[self.mongo_tb.battle_id]
        # FIXME
        reward_gold = this_stage.reward_gold
        reward_hero_id = self.mongo_tb.boss_id

        # for fid in self.mongo_tb.friend_ids:
        #     c = Char(fid)
        #     c.update(gold=reward_gold, des='TeamBattle Reward as friend')

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
        if self.mongo_tb:
            msg.team_battle.id = self.mongo_tb.battle_id
            msg.team_battle.boss_id = self.mongo_tb.boss_id
            msg.team_battle.boss_power = self.mongo_tb.boss_power
            msg.team_battle.self_power = self.mongo_tb.self_power

            msg.team_battle.start_at = self.mongo_tb.start_at
            msg.team_battle.step_progress = self.mongo_tb.step

            msg.team_battle.status = self.mongo_tb.status

            if self.mongo_tb.status == 3:
                this_stage = STAGE_CHALLENGE[self.mongo_tb.battle_id]
                # FIXME
                msg.team_battle.reward.gold = this_stage.reward_gold
                msg.team_battle.reward.heros.append(self.mongo_tb.boss_id)

        publish_to_char(self.char_id, pack_msg(msg))


timercheck.register(Hang)
timercheck.register(TeamBattle)
