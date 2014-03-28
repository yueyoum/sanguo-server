# -*- coding: utf-8 -*-

import logging
from random import randint, uniform, choice
from collections import defaultdict

from core.hero import FightPowerMixin, Hero


from mixins import ActiveEffectMixin, StepHeroNotifyMixin


from preset.settings import DEMAGE_VALUE_ADJUST
from preset.data import HEROS, MONSTERS, SKILLS

logger = logging.getLogger('battle')


class UsingEffect(object):
    __slots__ = ['id', 'value']
    def __init__(self, _id, value):
        self.id = _id
        self.value = value

class DieEvent(Exception):
    pass


class DizzinessEvent(Exception):
    pass



class DotEffectMixin(object):
    def active_dot_effects(self, target, eff, msg):
        if not (eff.id == 1 or eff.id == 2):
            return

        value = eff.value
        if eff.id == 1:
            value = -value
        target.set_hp(value)

        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = target.id
        hero_noti.hp = target.hp
        hero_noti.anger = target.anger

        hero_noti.value = value

        logger.debug("Dot %d, hp %d to Target %d. Hp %d, Anger %d" % (
            eff.id, value, target.id, target.hp, target.anger)
        )


class EffectManager(DotEffectMixin, StepHeroNotifyMixin):
    def __init__(self):
        self.effect_targets = defaultdict(lambda: [])
        self.effects = []

    def clean(self, msg):
        cleaned_effs = defaultdict(lambda: [])

        for h, effs in self.effect_targets.iteritems():
            for e in effs[:]:
                e.rounds -= 1
                if e.rounds <= 0:
                    self.effect_targets[h].remove(e)
                    h.effect_manager.effects.remove(e)
                    cleaned_effs[h].append(e.id)
                else:
                    self.active_dot_effects(h, e, msg)

        for k, v in cleaned_effs.iteritems():
            logger.debug("cleaned effs {0}: {1}".format(k.id, v))

            hero_noti = msg.hero_notify.add()
            hero_noti.target_id = k.id
            hero_noti.hp = k.hp
            hero_noti.anger = k.anger
            hero_noti.removes.extend(v)



    def add_effect_to_target(self, target, eff, msg):
        self.effect_targets[target].append(eff)
        target.effect_manager.add_effect(target, eff, msg)

        logger.debug("add effect %d to target %d" % (eff.id, target.id))


    def add_effect(self, me, eff, msg):
        self.effects.append(eff)
        self.fill_up_heor_notify(msg, me, eff)


    def effect_ids(self):
        return [e.id for e in self.effects]


class InBattleHero(ActiveEffectMixin, FightPowerMixin, DotEffectMixin):
    def __init__(self):
        # self._round = 0
        self.die = False
        self.max_hp = self.hp
        self.damage_value = 0
        self.effect_manager = EffectManager()


        self.default_skill = SKILLS[self.default_skill]
        self.skills = [SKILLS[i] for i in self.skills]
        self.attack_skills = []
        self.passive_skills = []

        for s in self.skills:
            if s.mode == 1:
                self.attack_skills.append(s)
            elif s.mode == 2:
                self.passive_skills.append(s)

    def __str__(self):
        return '<%d, %d, %d>' % (self.id, self.real_id, self.original_id)

    def set_hp(self, value):
        self.damage_value = value
        self.hp -= value
        self.hp = int(self.hp)
        if self.hp <= 0:
            self.hp = 0
            self.die = True

            return

        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def set_anger(self, value):
        self.anger += value
        if self.anger < 0:
            self.anger = 0
        if self.anger > 100:
            self.anger = 100


    def active_initiative_effects(self, msg):
        if self.die:
            raise DieEvent()

        for eff in self.effect_manager.effects:
            if eff.id == 9:
                raise DizzinessEvent()

        self.active_property_effects()


    def active_property_effects(self):
        # 效果所引起的属性变化
        # 当英雄被攻击时，需要先激活自身的效果
        # 用来计算属性变化
        self.using_attack = self.attack
        self.using_defense = self.defense
        self.using_crit = self.crit

        # 将同名效果的数值叠加
        reverse_id_table = {
            4: 3,
            6: 5,
            8: 7,
        }
        effects_id_values = {}
        for eff in self.effect_manager.effects:
            if eff.id in [1, 2, 9, 10, 11]:
                # logger.warning("active property effects: unsupported eff: {0}".format(eff.id))
                continue

            eff_id = eff.id
            eff_value = eff.value
            if eff_id in reverse_id_table:
                eff_id = reverse_id_table[eff_id]
                eff_value = -eff_value

            effects_id_values[eff_id] = effects_id_values.get(eff_id, 0) + eff_value

        for k, v in effects_id_values.iteritems():
            self.active_effect(self, UsingEffect(k, v))


    def find_skill(self, skills):
        # 计算是否触发技能
        # if not skills:
        #     return None

        # skill_probs = [[s.prob, s] for s in skills]
        #
        # for i in range(1, len(skill_probs)):
        #    skill_probs[i][0] += skill_probs[i-1][0]
        #
        # prob = randint(1, 100)
        # for _p, skill in skill_probs:
        #    if prob <= _p:
        #        return skill
        # return None

        # if not skills:
        #     return []
        #
        # active_skills = []
        # for s in skills:
        #     if (self._round - s.trig_start) % s.trig_cooldown == 0:
        #         active_skills.append(s)
        # return active_skills

        logger.debug("%d find skill. anger = %d" % (self.id, self.anger))
        if not skills:
            return [self.default_skill]

        if self.anger >= 100:
            self.anger -= 100
            return skills

        return [self.default_skill]




    def action(self, target):
        # self._round += 1
        # 英雄行动，首先清理本英雄所施加在其他人身上的效果
        msg = self.ground_msg.steps.add()
        msg.id = self.id

        self.effect_manager.clean(msg)

        if self.die:
            logger.debug("%d: die, return" % self.id)
            return

        try:
            self.active_initiative_effects(msg)
        except DieEvent:
            logger.debug("%d: die, return" % self.id)
            return
        except DizzinessEvent:
            logger.debug("%d: dizziness, return" % self.id)
            return
        #
        # hero_noti = msg.hero_notify.add()
        # hero_noti.target_id = self.id
        # hero_noti.hp = self.hp

        # skill = self.find_skill(self.attack_skills)
        #
        # if skill is None:
        #     logger.debug("%d: normal action" % self.id)
        #     self.normal_action(target, msg)
        # else:
        #     logger.debug("%d: skill action %d" % (self.id, skill.id))
        #     self.skill_action(target, skill, msg)

        # skills = self.find_skill(self.attack_skills)
        #
        # if not skills:
        #     logger.debug("%d: normal action" % self.id)
        #     self.normal_action(target, msg)
        # else:
        #     logger.debug("%d: skill action" % self.id)
        #     for skill in skills:
        #         logger.debug("%d: skill action %d. rounds = %d" % (self.id, skill.id, self._round))
        #         self.skill_action(target, skill, msg)

        skills = self.find_skill(self.attack_skills)
        for skill in skills:
            logger.debug("%d: skill action %d" % (self.id, skill.id))
            self.skill_action(target, skill, msg)


    #
    # def normal_action(self, target, msg):
    #     self._one_action(target, self.using_attack, msg)


    def real_damage_value(self, damage, target):
        m = 0.015  # 等级压制
        damage_reduce = min(0.02 * target.using_defense / (self.level + 9) + m * (target.level - self.level), 0.85)
        damage_reduce = max(damage_reduce, -0.15)
        value = damage * (1 - damage_reduce)

        # 攻击修正
        if self.HERO_TYPE == 1 and target.HERO_TYPE == 1:
            self_tp = HEROS[self.original_id].tp
            target_tp = HEROS[target.original_id].tp
            modulus = DEMAGE_VALUE_ADJUST[self_tp][target_tp]

            value += value * modulus

        return value


    def _one_action(self, target, value, msg, eff=None):
        target.active_property_effects()
        msg_target = msg.action.targets.add()
        msg_target.target_id = target.id
        msg_target.is_crit = False
        if self.using_crit >= randint(1, 100):
            msg_target.is_crit = True
            value *= 2

        text = "{0} => {1}, Eff: {2}, Crit: {3}".format(self.id, target.id, eff.id if eff else 'None', msg_target.is_crit)
        logger.debug(text)

        if not eff or eff.id == 2:
            value = self.real_damage_value(value, target) * uniform(0.97, 1.03)

        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = target.id

        value = int(value)
        target.set_hp(value)

        hero_noti.hp = target.hp
        hero_noti.value = value
        hero_noti.anger = target.anger

        if eff:
            e = hero_noti.adds.add()
            e.id =eff.id
            e.value = eff.value

        text = 'Value: {0}, Hp: {1}, Anger: {2}, Eff: {3}'.format(value, target.hp, target.anger, eff.id if eff else 'None')
        logger.debug(text)


    def get_effect_target(self, eff, target):
        def _team(hero):
            return [h for h in hero._team if h is not None and not h.die]

        if eff.target == 1:
            # 敌单体
            return [target]
        if eff.target == 2:
            # 自己
            return [self]
        if eff.target == 3:
            # 敌全体
            return _team(target)
        if eff.target == 4:
            # 己全体
            return _team(self)
        if eff.target == 5:
            # 敌随机一个
            team = _team(target)
            if not team:
                return []
            return [choice(team)]
        if eff.target == 6:
            # 敌随机两个
            team = _team(target)
            if len(team) <= 2:
                return team
            res = []
            for i in range(2):
                h = choice(team)
                team.remove(h)
                res.append(h)
            return res
        if eff.target == 7:
            # 己随机一个
            team = _team(self)
            if not team:
                return []
            return [choice(team)]
        if eff.target == 8:
            # 己随机两个
            team = _team(self)
            if len(team) <= 2:
                return team
            res = []
            for i in range(2):
                h = choice(team)
                team.remove(h)
                res.append(h)
            return res



    def skill_action(self, target, skill, msg):
        self.add_anger_to_target(skill, self, msg)

        msg.action.skill_id = skill.id
        effects = [eff.copy() for eff in skill.effects]
        zero_rounds_effects = []
        for eff in effects[:]:
            if eff.rounds == 0:
                zero_rounds_effects.append(eff)
                effects.remove(eff)


        for eff in effects:
            targets = self.get_effect_target(eff, target)
            logger.debug("Eff: {0}, targets: {1}".format(eff.id, [i.id for i in targets]))

            for t in targets:
                self.effect_manager.add_effect_to_target(t, eff, msg)
                if eff.id == 1 or eff.id == 2:
                    self.active_dot_effects(t, eff, msg)

                self.add_anger_to_target(skill, t, msg)

        for eff in zero_rounds_effects:
            if eff.id not in [1, 2]:
                raise Exception("Skill Action: Unsupported Zero rounds effect: {0}".format(eff.id))

            if eff.id == 1:
                # value = self.using_attack
                raise Exception("Skill Action: Unsupported Eff id: 1")
            elif eff.id == 2:
                value = self.using_attack * eff.value  / 100.0

            targets = self.get_effect_target(eff, target)
            logger.debug("Eff: {0}, targets: {1}".format(eff.id, [i.id for i in targets]))

            for t in targets:
                self._one_action(t, value, msg, eff)

                self.add_anger_to_target(skill, t, msg)


    def add_anger_to_target(self, skill, target, msg):
        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = target.id
        hero_noti.hp = target.hp

        if target.id == self.id:
            using_anger = skill.anger_self
        elif target in self._team:
            using_anger = skill.anger_self_team
        else:
            using_anger = skill.anger_rival_team

        target.set_anger(using_anger)

        hero_noti.anger = target.anger

        text = '{0} add anger {1} to {2}. Anger: {3}'.format(self.id, using_anger, target.id, target.anger)
        logger.debug(text)



class BattleHero(InBattleHero):
    HERO_TYPE = 1

    def __init__(self, _id):
        hero = Hero.cache_obj(_id)
        self.id = _id
        self.real_id = _id
        self.original_id = hero.oid
        self.attack = hero.attack
        self.defense = hero.defense
        self.hp = hero.hp
        self.crit = hero.crit
        self.dodge = 0

        self.anger = hero.anger

        self.level = hero.level
        self.skills = hero.skills

        self.default_skill = hero.default_skill

        super(BattleHero, self).__init__()


class BattleMonster(InBattleHero):
    HERO_TYPE = 2

    def __init__(self, mid):
        info = MONSTERS[mid]
        self.id = mid
        self.real_id = mid
        self.original_id = mid
        self.attack = info.attack
        self.defense = info.defense
        self.hp = info.hp
        self.crit = info.crit
        self.dodge = 0

        self.anger = info.anger

        self.skills = [int(i) for i in  info.skills.split(',')]
        self.level = info.level

        self.default_skill = info.default_skill

        super(BattleMonster, self).__init__()


