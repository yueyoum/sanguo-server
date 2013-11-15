# -*- coding: utf-8 -*-

import logging
from random import randint
from collections import defaultdict

from core.hero import Hero
from core import GLOBAL


logger = logging.getLogger('battle')


class DieEvent(Exception):
    pass

class DizzinessEvent(Exception):
    pass


class EffectManager(object):
    def __init__(self):
        self.effect_targets = defaultdict(lambda: [])
        self.effects = []


    def clean(self):
        cleaned_effs = defaultdict(lambda: [])

        for h, effs in self.effect_targets.iteritems():
            for e in effs[:]:
                e.rounds -= 1
                if e.rounds <= 0:
                    self.effect_targets[h].remove(e)
                    h.effect_manager.effects.remove(e)
                    cleaned_effs[h.id].append(e.type_id)

        logger.debug("cleaned_effs = {0}".format(cleaned_effs.items()))


    def add_effect_to_target(self, target, eff, msg):
        self.effect_targets[target].append(eff)
        target.effect_manager.add_effect(target, eff, msg)

        logger.debug("add effect %d to target %d" % (eff.type_id, target.id))


    def add_effect(self, me, eff, msg):
        self.effects.append(eff)
        hero_notify = msg.hero_notify.add()
        hero_notify.target_id = me.id
        hero_notify.hp = me.hp
        hero_notify.eff = eff.type_id
        hero_notify.buffs.extend(self.effect_ids())


    def effect_ids(self):
        return [e.type_id for e in self.effects]




def _logger_one_action(func):
    def deco(self, target, *args, **kwargs):
        msg_target, hero_notify = func(self, target, *args, **kwargs)
        text = "%d => %d, Crit: %s, Dodge: %s" % (
                self.id,
                target.id,
                msg_target.is_crit,
                msg_target.is_dodge
                )
        if not msg_target.is_dodge:
            text = '%s. Damage: %d, Hp: %d, Eff: %s' % (
                    text,
                    hero_notify.value,
                    target.hp,
                    str(hero_notify.eff) if hero_notify.eff else 'None'
                    )

        text = '%s. Target effects: %s' % (
                text,
                str(target.effect_manager.effect_ids())
                )

        logger.debug(text)
        return msg_target, hero_notify
    return deco


class InBattleHero(object):
    def __init__(self):
        self.die = False
        self.max_hp = self.hp
        self.damage_value = 0
        self.effect_manager = EffectManager()

        self.skills = [GLOBAL.SKILLS[sid] for sid in self.skills]
        self.attack_skills = []
        self.defense_skills = []
        self.passive_skills = []
        self.combine_skills = []


        for s in self.skills:
            if s.mode == 1:
                self.attack_skills.append(s)
            elif s.mode == 2:
                self.defense_skills.append(s)
            elif s.mode == 3:
                self.passive_skills.append(s)
            elif s.mode == 4:
                self.combine_skills.append(s)

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


    def cal_fighting_power(self):
        return 100


    def active_initiative_effects(self, msg):
        # 当英雄行动时，需要主动激活的效果
        # 比如持续伤害，治疗

        in_dizziness = False
        for eff in self.effect_manager.effects:
            if eff.type_id == 11:
                in_dizziness = True

            if eff.type_id == 1:
                # 持续加血
                value = int(eff.active_value)
                self.set_hp(-value)

                hero_notify = msg.hero_notify.add()
                hero_notify.target_id = self.id
                hero_notify.hp = self.hp
                hero_notify.eff = 1
                hero_notify.value = value

                logger.debug("Dot Add hp %d to Target %d. Hp %d" % (
                    value, self.id, self.hp)
                    )

            elif eff.type_id == 2:
                # 持续伤害
                value = int(eff.active_value)
                self.set_hp(value)

                hero_notify = msg.hero_notify.add()
                hero_notify.target_id = self.id
                hero_notify.hp = self.hp
                hero_notify.eff = 2
                hero_notify.value = value

                logger.debug("Dot Damage %d to Target %d. Hp %d" % (
                    value, self.id, self.hp)
                    )

                if self.hp <= 0:
                    raise DieEvent()

        if in_dizziness:
            raise DizzinessEvent()

        self.active_property_effects()

    


    def active_property_effects(self):
        # 效果所引起的属性变化
        # 当英雄被攻击时，需要先激活自身的效果
        # 用来计算属性变化
        self.using_attack = self.attack
        self.using_defense = self.defense
        self.using_crit = self.crit
        self.using_dodge = self.dodge

        for eff in self.effect_manager.effects:
            if eff.type_id == 1 or eff.type_id == 2 or eff.type_id == 11:
                pass

            elif eff.type_id == 3:
                self.using_attack += eff.value / 100.0 * self.using_attack
            elif eff.type_id == 4:
                self.using_attack -= eff.value / 100.0 * self.using_attack
            elif eff.type_id == 5:
                self.using_defense += eff.value / 100.0 * self.using_defense
            elif eff.type_id == 6:
                self.using_defense -= eff.value / 100.0 * self.using_defense
            elif eff.type_id == 7:
                self.using_dodge += eff.value / 100.0 * self.using_dodge
            elif eff.type_id == 8:
                self.using_dodge -= eff.value / 100.0 * self.using_dodge
            elif eff.type_id == 9:
                self.using_crit += eff.value / 100.0 * self.using_crit
            elif eff.type_id == 10:
                self.using_crit -= eff.value / 100.0 * self.using_crit
            else:
                raise TypeError("using_effects, Unsupported eff: %d" % eff.type_id)


    def find_prob(self, skills, base=70):
        # 计算是否触发技能
        if not skills:
            return None

        skill_probs = [[s.trig_prob, s] for s in skills]
        skill_probs.sort(key=lambda item: item[0])
        skill_probs[0][0] += base
        for i in range(1, len(skill_probs)):
            skill_probs[i][0] += skill_probs[i-1][0]

        prob = randint(1, skill_probs[-1][0])
        if prob <= base:
            return None

        for _p, skill in skill_probs:
            if prob <= _p:
                return skill


    def action(self, target):
        # 英雄行动，首先清理本英雄所施加在其他人身上的效果
        self.effect_manager.clean()

        if self.die:
            logger.debug("%d: die, return" % self.id)
            return

        msg = self.ground_msg.actions.add()
        msg.from_id = self.id

        try:
            self.active_initiative_effects(msg)
        except DieEvent:
            logger.debug("%d: die, return" % self.id)
            return
        except DizzinessEvent:
            logger.debug("%d: dizziness, return" % self.id)
            return

        
        hero_notify = msg.hero_notify.add()
        hero_notify.target_id = self.id
        hero_notify.hp = self.hp
        hero_notify.buffs.extend(self.effect_manager.effect_ids())


        skill = self.find_prob(self.attack_skills)

        if skill is None:
            logger.debug("%d: normal action" % self.id)
            self.normal_action(target, msg)
            rival_targets = [target]
        else:
            logger.debug("%d: skill action %d" % (self.id, skill.id))
            rival_targets = self.skill_action(target, skill, msg)

        logger.debug("rival targets = %s" % str([rt.id for rt in rival_targets]))
        for rt in rival_targets:
            self.start_defense_skills(rt, self, msg)

    def start_defense_skills(self, who, to, msg):
        skill = self.find_prob(who.defense_skills, base=0)
        if skill:
            _defense_action_msg = msg.passiveaction.add()
            _defense_action_msg.from_id = who.id
            _defense_action_msg.skill_id = skill.id
            logger.debug("Start Defense Skill %d, %d => %d" % (skill.id, who.id, to.id))
            who.active_initiative_effects(_defense_action_msg)
            who.skill_action(to, skill, _defense_action_msg)


    def real_damage_value(self, damage, target_defense):
        xx = min(0.024 * target_defense / (self.level + 9), 0.75)
        value = damage * (1 - xx)
        return value
        


    def normal_action(self, target, msg):
        target.active_property_effects()
        self._one_action(target, self.using_attack, msg)


    @_logger_one_action
    def _one_action(self, target, value, msg, eff=None):

        msg_target = msg.skill_targets.add()
        msg_target.target_id = target.id
        if self.using_crit >= randint(1, 100):
            value *= 2
            msg_target.is_crit = True
        else:
            msg_target.is_crit = False

        # FIXME
        if not eff or eff == 2:
            value = self.real_damage_value(value, target.using_defense)

        # target.active_property_effects()
        if not eff or eff not in [1, 12, 13]:
            # 加血，反伤，吸血不能闪避
            if target.using_dodge >= randint(1, 100):
                msg_target.is_dodge = True
                return msg_target, None

        msg_target.is_dodge = False
        hero_notify = msg.hero_notify.add()
        hero_notify.target_id = target.id

        value = int(value)
        if eff:
            if eff == 1 or eff == 13:
                value = -value
            else:
                if value < 0:
                    value = 0

    
        target.set_hp(value)

        hero_notify.hp = target.hp
        hero_notify.value = value

        if eff:
            hero_notify.eff = eff

        return msg_target, hero_notify



    def skill_action(self, target, skill, msg):
        msg.skill_id = skill.id
        effects = [eff.copy() for eff in skill.effects]

        immediately_effs = []

        rival_targets = set()

        for eff in effects[:]:
            if eff.rounds == 0:
                immediately_effs.append(eff)
                effects.remove(eff)

        _rival_targets = self.effect_influence(target, immediately_effs, msg)

        for eff in effects:
            if eff.type_id == 1:
                eff.active_value = eff.value
            elif eff.type_id == 2:
                eff.active_value = eff.value * self.using_attack / 100
            # FIXME 上面两种计算active_value 错误

            if eff.target == 1:
                if not target.die:
                    self.effect_manager.add_effect_to_target(target, eff, msg)
                    rival_targets.add(target)
            elif eff.target == 2:
                if not self.die:
                    self.effect_manager.add_effect_to_target(self, eff, msg)
            elif eff.target == 3:
                for _h in target._team:
                    if _h is None or _h.die:
                        continue

                    self.effect_manager.add_effect_to_target(_h, eff, msg)
                    rival_targets.add(_h)
            elif eff.target == 4:
                for _h in self._team:
                    if _h is None or _h.die:
                        continue

                    self.effect_manager.add_effect_to_target(_h, eff, msg)

        for _rt in _rival_targets:
            rival_targets.add(_rt)

        return rival_targets



    def effect_influence(self, target, immediately_effs, msg):
        rival_targets = set()

        for eff in immediately_effs:
            eff_target = []
            if eff.target == 1:
                if not target.die:
                    eff_target = [target]
                    rival_targets.add(target)
            elif eff.target == 2:
                if not self.die:
                    eff_target = [self]
            elif eff.target == 3:
                eff_target = [t for t in target._team if t is not None and not t.die]
                for t in eff_target:
                    rival_targets.add(t)
            else:
                eff_target = [t for t in self._team if t is not None and not t.die]

            for t in eff_target:
                t.active_property_effects()
                if eff.type_id == 1:
                    self._one_action(t, eff.value * t.hp / 100, msg, 1)
                elif eff.type_id == 2:
                    self._one_action(t, eff.value * self.using_attack / 100, msg, 2)
                elif eff.type_id == 12:
                    self._one_action(t, eff.value * self.damage_value / 100, msg, 12)
                elif eff.type_id == 13:
                    value = eff.value * self.using_attack / 100
                    self._one_action(t, value, msg, 13)
                    t._one_action(self, value, msg, 13)
                else:
                    raise TypeError("UnSupported Effect Type: %d" % eff.type_id)

        return [rt for rt in rival_targets if not rt.die]




class BattleHero(Hero, InBattleHero):
    _hero_type = 1
    def __init__(self, *args, **kwargs):
        Hero.__init__(self, *args, **kwargs)
        InBattleHero.__init__(self)



class MonsterHero(InBattleHero):
    _hero_type = 2

    def __init__(self, mid):
        info = GLOBAL.MONSTERS[mid]
        self.id = mid
        self.original_id = mid
        self.attack = info['attack']
        self.defense = info['defense']
        self.hp = info['hp']
        self.crit = info['crit']
        self.dodge = info['dodge']
        self.skills = info['skills']

        InBattleHero.__init__(self)

