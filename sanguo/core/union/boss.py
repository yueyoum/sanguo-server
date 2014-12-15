# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-10'

import json
import arrow

from mongoengine import DoesNotExist
from core.mongoscheme import MongoUnionBoss, MongoEmbeddedUnionBoss, MongoEmbeddedUnionBossLog
from core.exception import SanguoException
from core.union.base import UnionLoadBase, union_instance_check
from core.union.union import UnionBase, UnionOwner
from core.union.member import Member

from core.attachment import make_standard_drop_from_template, standard_drop_to_attachment_protomsg
from core.mail import Mail
from core.character import Char

from core.battle.hero import InBattleHero
from core.battle.battle import Ground
from core.battle import PVE

from preset import errormsg
from preset.data import UNION_BOSS, UNION_BOSS_REWARD

import protomsg


UNION_BOSS_KILLER_REWARD = UNION_BOSS_REWARD.pop(0)


class UnionBoss(UnionLoadBase):
    def __init__(self, char_id):
        super(UnionBoss, self).__init__(char_id)
        if isinstance(self.union, UnionBase):
            self.load_data()


    def load_data(self):
        try:
            self.mongo_boss = MongoUnionBoss.objects.get(id=self.union.union_id)
        except DoesNotExist:
            self.mongo_boss = MongoUnionBoss(id=self.union.union_id)
            self.mongo_boss.opened = {}
            self.mongo_boss.save()

        self.member = Member(self.char_id)


    @property
    def max_times(self):
        return 3

    @property
    def cur_times(self):
        return self.member.mongo_union_member.boss_times

    def incr_battle_times(self):
        self.member.mongo_union_member.boss_times += 1
        self.member.mongo_union_member.save()

    @union_instance_check(UnionOwner, errormsg.UNION_BOSS_ONLY_OPENED_BY_OWNER, "UnionBoss Start", "not owner")
    def start(self, boss_id):
        try:
            boss = UNION_BOSS[boss_id]
        except KeyError:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionBoss Start",
                "boss {0} not exist".format(boss_id)
            )

        if self.union.mongo_union.level < boss.union_level:
            raise SanguoException(
                errormsg.UNION_BOSS_LEVEL_NOT_ENOUGH,
                self.char_id,
                "UnionBoss Start",
                "union level not enough. {0} < {1}".format(self.union.mongo_union.level, boss.union_level)
            )

        meb = MongoEmbeddedUnionBoss()
        meb.start_at = arrow.utcnow().timestamp
        meb.hp = boss.hp
        meb.logs = []

        self.mongo_boss.opened[str(boss_id)] = meb
        self.mongo_boss.save()


    @union_instance_check(UnionBase, errormsg.UNION_NOT_EXIST, "UnionBoss Battle", "has no union")
    def battle(self, boss_id):
        try:
            this_boss = self.mongo_boss.opened[str(boss_id)]
        except KeyError:
            raise SanguoException(
                errormsg.UNION_BOSS_NOT_STARTED,
                self.char_id,
                "UnionBoss Battle",
                "boss not started {0}".format(boss_id)
            )

        if this_boss.hp <= 0:
            raise SanguoException(
                errormsg.UNION_BOSS_DEAD,
                self.char_id,
                "UnionBoss Battle",
                "boss dead {0}".format(boss_id)
            )

        if self.cur_times >= self.max_times:
            raise SanguoException(
                errormsg.UNION_BOSS_NO_TIMES,
                self.char_id,
                "UnionBoss Battle",
                "no times"
            )


        msg = protomsg.Battle()
        battle = UnionBossBattle(self.char_id, boss_id, msg, this_boss.hp)
        remained_hp = battle.start()

        this_boss.hp = remained_hp

        eubl = MongoEmbeddedUnionBossLog()
        eubl.char_id = self.char_id
        eubl.damage = battle.get_total_damage()

        this_boss.logs.append(eubl)
        self.mongo_boss.save()

        self.incr_battle_times()
        drop_msg = self.after_battle(boss_id, eubl.damage, remained_hp<=0)

        if remained_hp <= 0:
            self.boss_has_been_killed(boss_id)

        return msg, drop_msg


    def after_battle(self, boss_id, damage, kill=False):
        # 每次打完给予奖励
        member = Member(self.char_id)
        boss = UNION_BOSS[boss_id]
        contribute_points = int( float(damage)/boss.hp * boss.contribute_points )
        lowest = 1
        highest = int(boss.contribute_points * 0.05)
        if contribute_points < lowest:
            contribute_points = lowest
        if contribute_points > highest:
            contribute_points = highest

        coin = 9 + contribute_points

        member.add_coin(coin, send_notify=False)
        member.add_contribute_points(contribute_points, send_notify=True)
        if not kill:
            self.union.add_contribute_points(contribute_points)

        drop = make_standard_drop_from_template()
        drop['union_coin'] = coin
        drop['union_contribute_points'] = contribute_points
        return standard_drop_to_attachment_protomsg(drop)


    def boss_has_been_killed(self, boss_id):
        # 击杀boss后发送奖励
        logs = self.get_battle_members_in_ordered(boss_id)
        member_ids = [log.char_id for log in logs]

        killer = self.char_id

        m = Mail(killer)
        drop = make_standard_drop_from_template()
        drop['union_coin'] = UNION_BOSS_KILLER_REWARD.coin
        m.add(
            UNION_BOSS_KILLER_REWARD.mail_title,
            UNION_BOSS_KILLER_REWARD.mail_content,
            attachment=json.dumps(drop)
            )

        LOWEST_RANK = max(UNION_BOSS_REWARD.keys())
        UNION_BOSS_REWARD_TUPLE = UNION_BOSS_REWARD.items().sort(key=lambda item: item[0])

        for index, mid in enumerate(member_ids):
            rank = index + 1
            if rank > LOWEST_RANK:
                break

            m = Mail(mid)

            for _rank, _reward in UNION_BOSS_REWARD_TUPLE:
                if _rank >= rank:
                    drop = make_standard_drop_from_template()
                    drop['union_coin'] = _reward.coin
                    m.add(
                        _reward.mail_title.format(rank),
                        _reward.mail_content.format(rank),
                        attachment=json.dumps(drop)
                    )

                    break

        # 工会获得贡献度
        self.union.add_contribute_points(UNION_BOSS[boss_id].contribute_points)


    def get_battle_members_in_ordered(self, boss_id):
        this_boss = self.mongo_boss.opened[str(boss_id)]
        return sorted(this_boss.logs, key=lambda item: -item.damage)


    @union_instance_check(UnionBase, errormsg.UNION_NOT_EXIST, "UnionBoss Get Log", "has no union")
    def make_log_message(self, boss_id):
        try:
            this_boss = self.mongo_boss.opened[str(boss_id)]
        except KeyError:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "UnionBoss Get Log",
                "no log for boss {0}".format(boss_id)
            )

        hp = float(UNION_BOSS[boss_id].hp)

        msg = protomsg.UnionBossGetLogResponse()
        msg.ret = 0
        msg.boss_id = boss_id
        for log in self.get_battle_members_in_ordered(boss_id):
            msg_log = msg.logs.add()
            msg_log.char_id = log.char_id
            msg_log.char_name = Char(log.char_id).mc.name
            msg_log.damage = log.damage
            msg_log.precent = int(log.damage/hp * 100)

        if this_boss.hp <= 0:
            this_boss.killer.MergeFrom(msg.logs[-1])

        return msg


    @union_instance_check(UnionBase, errormsg.UNION_NOT_EXIST, "UnionBoss Response", "has no union")
    def make_boss_response(self):
        msg = protomsg.UnionBossResponse()
        msg.ret = 0
        msg.remained_times = self.max_times - self.cur_times

        union_level = self.union.mongo_union.level
        available_bosses = [k for k, v in UNION_BOSS.items() if union_level >= v.union_level]

        for b in available_bosses:
            msg_boss = msg.bosses.add()
            msg_boss.id = b

            if str(b) not in self.mongo_boss.opened:
                msg_boss.hp = UNION_BOSS[b].hp
                msg_boss.status = protomsg.UnionBossResponse.Boss.INACTIVE
            else:
                this_boss = self.mongo_boss.opened[str(b)]
                msg_boss.hp = this_boss.hp

                if this_boss.hp <= 0:
                    msg_boss.status = protomsg.UnionBossResponse.Boss.DEAD
                else:
                    msg_boss.status = protomsg.UnionBossResponse.Boss.ACTIVE

        return msg



class BattleBoss(InBattleHero):
    HERO_TYPE = 3
    def __init__(self, boss_id):
        info = UNION_BOSS[boss_id]
        self.id = boss_id
        self.real_id = boss_id
        self.original_id = boss_id

        self.attack = info.attack
        self.defense = info.defense
        self.hp = info.hp
        self.crit = info.crit
        self.dodge = 0

        self.anger = 0
        self.default_skill = info.default_skill
        self.skills = [info.skill]
        self.skill_release_rounds = info.skill_rounds
        self.level = 0

        super(BattleBoss, self).__init__()

    def find_skill(self, skills):
        if self._round % self.skill_release_rounds == 0:
            return skills
        return [self.default_skill]

    def real_damage_value(self, damage, target):
        return damage

    def _one_action_on_target(self, target, value):
        value = -target.hp
        target.set_hp(value)
        return value


class UnionBossBattle(PVE):
    BATTLE_TYPE = 'UNION_BOSS'
    def __init__(self, my_id, rival_id, msg, boss_init_hp):
        super(UnionBossBattle, self).__init__(my_id, rival_id, msg)
        self.msg.rival_power /= 3
        self.boss_init_hp = boss_init_hp

    def load_rival_heros(self):
        bosses = [
            0, BattleBoss(self.rival_id), 0,
            0, BattleBoss(self.rival_id), 0,
            0, BattleBoss(self.rival_id), 0,
        ]

        rival_heros = []
        for b in bosses:
            if b == 0:
                rival_heros.append(None)
            else:
                rival_heros.append(b)

        return rival_heros

    def get_rival_name(self):
        return UNION_BOSS[self.rival_id].name

    def start(self):
        msgs = [self.msg.first_ground, self.msg.second_ground, self.msg.third_ground]
        win_count = 0

        def _recover_hp(i):
            boss = self.rival_heros[i]
            _hp = int( boss.total_damage_value * 0.05 )
            boss.hp += _hp
            return boss.hp

        for index in range(3):
            # index = 0, 1 ,2
            # boss = self.rival_heros [1, 4, 7]
            # old_boss = self.rival_heros [ (index-1)*3 + 1 ]
            # cur_boss = self.rival_heros [ index*3 + 1 ]
            my_heros = self.my_heros[index*3:index*3+3]
            rival_heros = self.rival_heros[index*3:index*3+3]
            if index == 0:
                rival_heros[1].hp = self.boss_init_hp
            else:
                # 生命值继承自上一场战斗
                rival_heros[1].hp = _recover_hp((index-1)*3+1)

            g = Ground(my_heros, rival_heros, msgs[index])
            g.index = index + 1
            win = g.start()
            if win:
                win_count += 1

        if win_count > 2:
            self.msg.self_win = True
        else:
            self.msg.self_win = False

        if self.msg.self_win:
            return 0
        return _recover_hp(7)

    def get_total_damage(self):
        return self.rival_heros[1].total_damage_value + \
            self.rival_heros[4].total_damage_value + \
            self.rival_heros[7].total_damage_value

