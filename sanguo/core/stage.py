# -*- coding: utf-8 -*-
import random

from mongoengine import DoesNotExist
from apps.hero.models import Hero as ModelHero
from apps.stage.models import Stage as ModelStage, EliteStage as ModelEliteStage, ChallengeStage as ModelChallengeStage
from apps.stage.models import StageDrop
from core.mongoscheme import MongoStage, MongoTeamBattle

from utils import timezone
from utils import pack_msg
from core.msgpipe import publish_to_char
from core.attachment import Attachment
from core.achievement import Achievement
from core.task import Task

import protomsg

from core.exception import InvalidOperate, SanguoException, SyceeNotEnough, StuffNotEnough
from core.battle import PVE, ElitePVE

from core.mongoscheme import MongoHang, MongoEmbededPlunderLog
from core.counter import Counter
from core.character import Char
from core.friend import Friend
from core.hero import save_hero
from core.item import Item
from core.timercheck import TimerCheckAbstractBase, timercheck

# from worker import tasks
from utils.math import GAUSSIAN_TABLE

from preset.settings import TEAMBATTLE_INCR_COST

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

            # 开启精英关卡
            elite = EliteStage(self.char_id)
            elite.enable_by_condition_id(stage_id)

            if stage_id == 10:
                achievement = Achievement(self.char_id)
                achievement.trig(6, 1)

            t = Task(self.char_id)
            t.trig(1)


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
        attach.save_to_char(exp=exp, gold=gold, stuffs=stuffs)

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



class Hang(TimerCheckAbstractBase):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.hang = MongoHang.objects.get(id=self.char_id)
            if self.hang.finished:
                self.send_prize_notify()
        except DoesNotExist:
            self.hang = None


    def check(self):
        if not self.hang or self.hang.finished:
            return

        counter = Counter(self.char_id, 'hang')
        remained_seconds = counter.remained_value
        if timezone.utc_timestamp() - self.hang.start >= remained_seconds:
            # finish
            self.finish(actual_seconds=remained_seconds)


    def start(self, stage_id):
        if self.hang:
            raise SanguoException(700, "Hang Start: Char {0} Try to a Multi hang".format(self.char_id))

        counter = Counter(self.char_id, 'hang')
        remained_seconds = counter.remained_value

        if remained_seconds <= 0:
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
            # jobid=job.id,
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

        self.hang.logs.append(l)
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
        a.save_to_char(exp=exp, gold=gold, stuffs=stuffs)
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
            this_stage = ModelEliteStage.all()[_id]
        except KeyError:
            raise InvalidOperate("EliteStage Battle. Char {0} try to battle a NONE exists elite stage {1}".format(self.char_id, _id))

        if times >= this_stage.times:
            raise InvalidOperate("EliteStage Battle. Char {0}. already times {1}. condition times {2}".format(
                self.char_id, times, this_stage.times
            ))

        battle_msg = protomsg.Battle()
        b = ElitePVE(self.char_id, _id, battle_msg)
        b.start()

        if battle_msg.self_win:
            self.stage.elites[str_id] += 1
            self.stage.save()

            msg = protomsg.UpdateEliteStageNotify()
            msg.stage.id = _id
            msg.stage.current_time = self.stage.elites[str_id]
            publish_to_char(self.char_id, pack_msg(msg))

        return battle_msg


    def get_drop(self):
        pass

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
        if not self.mongo_tb:
            return

        if timezone.utc_timestamp() - self.mongo_tb.start_at >= self.mongo_tb.total_seconds:
            # FINISH
            self.mongo_tb.status = 3
            self.mongo_tb.save()
            self.send_notify()

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
        if item.has_stuff(need_stuff_id, need_stuff_amount):
            raise StuffNotEnough("TeamBattle Enter. Char {0} Try to enter battle {1}. But stuff not enough".format(self.char_id, _id))

        item.stuff_remove(need_stuff_id, need_stuff_amount)


        boss_id = ModelHero.get_by_grade(this_stage.level)
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

        friend_power = 0
        if friend_ids:
            f = Friend(self.char_id)
            for fid in friend_ids:
                if not f.is_friend(fid):
                    raise InvalidOperate("TeamBattle Start. Char {0} has no friend {1}".format(self.char_id, fid))

                c = Char(fid)
                friend_power += c.power

        self.mongo_tb.friend_ids.extend(friend_ids)
        self.mongo_tb.self_power += friend_power
        self.mongo_tb.start_at = timezone.utc_timestamp()
        self.mongo_tb.status = 2
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

        char.update(sycee=-TEAMBATTLE_INCR_COST)

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
            c.update(gold=reward_gold)

        c = Char(self.char_id)
        c.update(gold=reward_gold)
        save_hero(self.char_id, reward_hero_id)

        self.mongo_tb.delete()
        self.mongo_tb = None
        self.send_notify()

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

            step_progress = self.mongo_tb.self_power / self.mongo_tb.boss_power * 0.0034
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
