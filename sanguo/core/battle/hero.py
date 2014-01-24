# -*- coding: utf-8 -*-

import logging
from random import randint, uniform
from collections import defaultdict

from core.hero import FightPowerMixin, Hero


from mixins import ActiveEffectMixin

from apps.hero.models import Monster
from apps.skill.models import Skill as ModelSkill

logger = logging.getLogger('battle')


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
        hero_noti.eff = eff.id
        hero_noti.value = value

        logger.debug("Dot %d, hp %d to Target %d. Hp %d" % (
            eff.id, value, target.id, target.hp)
        )


class EffectManager(DotEffectMixin):
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
                    cleaned_effs[h.id].append(e.id)
                else:
                    self.active_dot_effects(h, e, msg)

        logger.debug("cleaned_effs = {0}".format(cleaned_effs.items()))


    def add_effect_to_target(self, target, eff, msg):
        self.effect_targets[target].append(eff)
        target.effect_manager.add_effect(target, eff, msg)

        logger.debug("add effect %d to target %d" % (eff.id, target.id))


    def add_effect(self, me, eff, msg):
        self.effects.append(eff)

        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = me.id
        hero_noti.hp = me.hp
        hero_noti.eff = eff.id
        hero_noti.buffs.extend(self.effect_ids())


    def effect_ids(self):
        return [e.id for e in self.effects]


class InBattleHero(ActiveEffectMixin, FightPowerMixin, DotEffectMixin):
    def __init__(self):
        self.die = False
        self.max_hp = self.hp
        self.damage_value = 0
        self.effect_manager = EffectManager()


        all_skills = ModelSkill.all()
        self.skills = [all_skills[i] for i in self.skills]
        self.attack_skills = []
        self.passive_skills = []

        for s in self.skills:
            if s.mode == 1:
                self.attack_skills.append(s)
            elif s.mode == 2:
                self.passive_skills.append(s)

    def __str__(self):
        return '<%d, %d>' % (self.id, self.original_id)

    def set_hp(self, value):
        self.damage_value = value
        self.hp -= value
        if self.hp <= 0:
            self.hp = 0
            self.die = True

            return

        if self.hp > self.max_hp:
            self.hp = self.max_hp



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

        for eff in self.effect_manager.effects:
            if eff.id in [1, 2, 9, 10, 11]:
                logger.warning("active property effects: unsupported eff: {0}".format(eff.id))
                continue

            self.active_effect(self, eff)


    def find_skill(self, skills):
        # 计算是否触发技能
        if not skills:
            return None

        skill_probs = [[s.prob, s] for s in skills]

        for i in range(1, len(skill_probs)):
           skill_probs[i][0] += skill_probs[i-1][0]

        prob = randint(1, skill_probs[-1][0])
        for _p, skill in skill_probs:
           if prob <= _p:
               return skill
        return None


    def action(self, target):
        # 英雄行动，首先清理本英雄所施加在其他人身上的效果
        if self.die:
            logger.debug("%d: die, return" % self.id)
            return

        msg = self.ground_msg.actions.add()
        msg.from_id = self.id

        self.effect_manager.clean(msg)

        try:
            self.active_initiative_effects(msg)
        except DieEvent:
            logger.debug("%d: die, return" % self.id)
            return
        except DizzinessEvent:
            logger.debug("%d: dizziness, return" % self.id)
            return

        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = self.id
        hero_noti.hp = self.hp
        hero_noti.buffs.extend(self.effect_manager.effect_ids())

        skill = self.find_skill(self.attack_skills)

        if skill is None:
            logger.debug("%d: normal action" % self.id)
            self.normal_action(target, msg)
        else:
            logger.debug("%d: skill action %d" % (self.id, skill.id))
            self.skill_action(target, skill, msg)


    def normal_action(self, target, msg):
        self._one_action(target, self.using_attack, msg)


    def real_damage_value(self, damage, target):
        damage_reduce = min(0.02 * target.using_defense / (self.level + 9) + 0.015 * (target.level - self.level), 0.85)
        damage_reduce = max(damage_reduce, -0.15)
        value = damage * (1 - damage_reduce)
        return value


    def _one_action(self, target, value, msg, eff=None):
        target.active_property_effects()
        msg_target = msg.targets.add()
        msg_target.target_id = target.id
        msg_target.is_crit = False
        if self.using_crit >= randint(1, 100):
            msg_target.is_crit = True

        text = "{0} => {1}, Eff: {2}, Crit: {3}".format(self.id, target.id, eff.id, msg_target.is_crit)
        logger.debug(text)

        if not eff or eff == 2:
            value = self.real_damage_value(value, target) * uniform(0.97, 1.03)

        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = target.id

        value = int(value)
        target.set_hp(value)

        hero_noti.hp = target.hp
        hero_noti.value = value

        if eff:
            hero_noti.eff = eff.id

        text = 'Value: {0}, Hp: {1}, Eff: {2}'.format(value, target.hp, eff.id)
        logger.debug(text)


    def get_effect_target(self, eff, target):
        if eff.target == 1:
            return [target]
        if eff.target == 2:
            return [self]
        if eff.target == 3:
            return [h for h in target._team if h is not None and not h.die]
        return [h for h in self._team if h is not None and not h.die]


    def skill_action(self, target, skill, msg):
        msg.skill_id = skill.id
        effects = [eff.copy() for eff in skill.effects]
        zero_rounds_effects = []
        for eff in effects[:]:
            if eff.rounds == 0:
                zero_rounds_effects.append(eff)
                effects.remove(eff)


        for eff in effects:
            targets = self.get_effect_target(eff, target)
            for t in targets:
                self.effect_manager.add_effect_to_target(t, eff, msg)
                if eff.id == 1 or eff.id == 2:
                    self.active_dot_effects(t, eff, msg)

        for eff in zero_rounds_effects:
            if eff.id not in [1, 2]:
                logger.warning("Unsupported Zero rounds effect: {0}".format(eff.id))

            if eff.id == 1:
                value = self.using_attack
            elif eff.id == 2:
                value = self.hp * eff.value  / 100.0

            targets = self.get_effect_target(eff, target)
            for t in targets:
                self._one_action(t, value, msg, eff)





class BattleHero(InBattleHero):
    HERO_TYPE = 1

    def __init__(self, _id):
        hero = Hero.cache_obj(_id)
        self.id = _id
        self.original_id = hero.oid
        self.attack = hero.attack
        self.defense = hero.defense
        self.hp = hero.hp
        self.crit = hero.crit
        self.dodge = 0

        self.level = hero.level
        self.skills = hero.skills

        super(BattleHero, self).__init__()


class BattleMonster(InBattleHero):
    HERO_TYPE = 2

    def __init__(self, mid):
        info = Monster.all()[mid]
        self.id = mid
        self.original_id = mid
        self.attack = info.attack
        self.defense = info.defense
        self.hp = info.hp
        self.crit = info.crit
        self.dodge = 0
        self.skills = [int(i) for i in  info.skills.split(',')]
        self.level = info.level

        super(BattleMonster, self).__init__()


