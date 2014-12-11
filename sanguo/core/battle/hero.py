# -*- coding: utf-8 -*-

import logging
from random import randint, uniform, choice
from collections import defaultdict

from core.hero import FightPowerMixin, Hero, cal_monster_property
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


def _empty_step_msg_check(func):
    def deco(self, *args, **kwargs):
        msg = func(self, *args, **kwargs)
        if not msg.action.IsInitialized() and len(msg.hero_notify) == 0 and len(msg.dead_ids) == 0:
            # empty step msg, remove it
            self.ground_msg.steps.remove(msg)
        return msg
    return deco


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
            if h.die:
                # 对于死亡的人物是忽略掉，还是彻底的从effect_targets中移除？
                continue

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
        self._round = 1
        self.die = False
        self.max_hp = self.hp
        self.damage_value = 0
        self.total_damage_value = 0
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
        if value < 0:
            self.total_damage_value += int(abs(value))

        self.damage_value = value
        self.hp += value
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
        logger.debug("%d find skill. anger = %d" % (self.id, self.anger))
        if not skills:
            return [self.default_skill]

        if self.anger >= 100:
            self.anger -= 100
            return skills

        return [self.default_skill]


    @_empty_step_msg_check
    def action(self, target):
        self._round += 1
        # 英雄行动，首先清理本英雄所施加在其他人身上的效果
        msg = self.ground_msg.steps.add()
        msg.id = self.id

        self.effect_manager.clean(msg)

        if self.die:
            logger.debug("%d: die, return" % self.id)
            return msg

        try:
            self.active_initiative_effects(msg)
        except DieEvent:
            logger.debug("%d: die, return" % self.id)
            return msg
        except DizzinessEvent:
            logger.debug("%d: dizziness, return" % self.id)
            return msg

        skills = self.find_skill(self.attack_skills)
        for skill in skills:
            logger.debug("%d: skill action %d" % (self.id, skill.id))
            _dead_ids = self.skill_action(target, skill, msg)
            msg.dead_ids.extend(_dead_ids)

        return msg


    def real_damage_value(self, damage, target):
        # 等级压制
        if self.HERO_TYPE == 1 and target.HERO_TYPE == 1:
            m = 0
        else:
            m = 0.06

        damage_reduce = min(0.02 * target.using_defense / (self.level + 9) + m * (target.level - self.level), 0.85)
        damage_reduce = max(damage_reduce, -0.15)
        value = damage * (1 - damage_reduce)

        # 攻击修正
        if self.HERO_TYPE == 1:
            self_tp = HEROS[self.original_id].tp
        else:
            self_tp = MONSTERS[self.original_id].tp

        if target.HERO_TYPE == 1:
            target_tp = HEROS[target.original_id].tp
        else:
            target_tp = MONSTERS[target.original_id].tp

        modulus = DEMAGE_VALUE_ADJUST[self_tp][target_tp]

        value += value * modulus

        return value


    def _one_action(self, target, value, msg, eff):
        target.active_property_effects()

        is_crit = False
        if self.using_crit >= uniform(1, 100):
            is_crit = True
            value *= 2

        text = "{0} => {1}, Eff: {2}, Crit: {3}".format(self.id, target.id, eff.id if eff else 'None', is_crit)
        logger.debug(text)

        if eff.is_hit_target:
            msg_target = msg.action.targets.add()
            msg_target.target_id = target.id
            msg_target.is_crit = is_crit

        if eff.id == 2:
            value = self.real_damage_value(value, target) * uniform(0.97, 1.03)

        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = target.id

        value = int(value)
        self._one_action_on_target(target, value)

        hero_noti.hp = target.hp
        hero_noti.value = value
        hero_noti.anger = target.anger

        text = 'Value: {0}, Hp: {1}, Anger: {2}, Eff: {3}'.format(value, target.hp, target.anger, eff.id if eff else 'None')
        logger.debug(text)

    def _one_action_on_target(self, target, value):
        target.set_hp(value)


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

        dead_ids = []
        for eff in zero_rounds_effects:
            if eff.id not in [1, 2]:
                raise Exception("Skill Action: Unsupported Zero rounds effect: {0}".format(eff.id))

            if eff.id == 1:
                value = self.using_attack * eff.value  / 100.0
            elif eff.id == 2:
                value = -(self.using_attack * eff.value  / 100.0)

            targets = self.get_effect_target(eff, target)
            logger.debug("Eff: {0}, targets: {1}".format(eff.id, [i.id for i in targets]))

            for t in targets:
                if t.die:
                    continue

                self._one_action(t, value, msg, eff)
                if t.die:
                    dead_ids.append(t.id)
                else:
                    self.add_anger_to_target(skill, t, msg)

        return dead_ids


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

    def __init__(self, mid, level, strength_modulus):
        info = MONSTERS[mid]
        self.id = mid
        self.real_id = mid
        self.original_id = mid

        self.attack, self.defense, self.hp = cal_monster_property(mid, level)

        self.crit = info.crit
        self.dodge = 0

        self.attack = self.attack * strength_modulus
        self.defense = self.defense * strength_modulus
        self.hp = int(self.hp * strength_modulus)
        self.crit = self.crit * strength_modulus

        self.anger = info.anger

        self.skills = [int(i) for i in  info.skills.split(',')]
        self.level = level

        self.default_skill = info.default_skill

        super(BattleMonster, self).__init__()
