# -*- coding: utf-8 -*-

import logging
from random import randint
from collections import defaultdict

from core import GLOBAL
from core.hero import FightPowerMixin

from core.cache import get_cache_hero
from apps.character.cache import get_cache_character

from mixins import ActiveEffectMixin


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
        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = me.id
        hero_noti.hp = me.hp
        hero_noti.eff = eff.type_id
        hero_noti.buffs.extend(self.effect_ids())


    def effect_ids(self):
        return [e.type_id for e in self.effects]



class InBattleHero(ActiveEffectMixin, FightPowerMixin):
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


    def _dot_effects(self, eff, msg):
        value = eff.value
        if eff.type_id == 1:
            value = -value
        self.set_hp(value)

        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = self.id
        hero_noti.hp = self.hp
        hero_noti.eff = eff.type_id
        hero_noti.value = value
        
        logger.debug("Dot %d, hp %d to Target %d. Hp %d" % (
            eff.type_id, value, self.id, self.hp)
            )

    def active_initiative_effects(self, msg):
        # 当英雄行动时，需要主动激活的效果
        # 比如持续伤害，治疗

        in_dizziness = False
        for eff in self.effect_manager.effects:
            if eff.type_id == 11:
                in_dizziness = True

            if eff.type_id == 1:
                # 持续加血
                self._dot_effects(eff, msg)
            elif eff.type_id == 2:
                # 持续伤害
                self._dot_effects(eff, msg)
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
            if eff.type_id in [1, 2, 11]:
                continue
            
            if eff.type_id in [12, 13, 14]:
                raise TypeError("using_effects, Unsupported eff: %d" % eff.type_id)
            
            self._active_effect(self, eff)


    def find_skill(self, skills):
        # 计算是否触发技能
        if not skills:
            return None

        #skill_probs = [[s.trig_prob, s] for s in skills]
        #
        #for i in range(1, len(skill_probs)):
        #    skill_probs[i][0] += skill_probs[i-1][0]
        #
        #if skill_probs[-1][0] > 100:
        #    raise Exception("find_skill, {0}".format(skill_probs))
        #
        #
        #prob = randint(1, 100)
        #for _p, skill in skill_probs:
        #    if prob <= _p:
        #        return skill
        #return None
        
        for s in skills:
            if s.trig_prob >= randint(1, 100):
                return s
        
        return None
        


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

        
        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = self.id
        hero_noti.hp = self.hp
        hero_noti.buffs.extend(self.effect_manager.effect_ids())


        skill = self.find_skill(self.attack_skills)

        if skill is None:
            logger.debug("%d: normal action" % self.id)
            self.normal_action(target, msg)
            rival_targets = [target]
        else:
            logger.debug("%d: skill action %d" % (self.id, skill.id))
            rival_targets = self.skill_action(target, skill, msg)

    #    logger.debug("rival targets = %s" % str([rt.id for rt in rival_targets]))
    #    for rt in rival_targets:
    #        self.start_defense_skills(rt, self, msg)
    #
    #def start_defense_skills(self, who, to, msg):
    #    skill = self.find_skill(who.defense_skills, base=0)
    #    if skill:
    #        _defense_action_msg = msg.passiveaction.add()
    #        _defense_action_msg.from_id = who.id
    #        _defense_action_msg.skill_id = skill.id
    #        logger.debug("Start Defense Skill %d, %d => %d" % (skill.id, who.id, to.id))
    #        who.active_initiative_effects(_defense_action_msg)
    #        who.skill_action(to, skill, _defense_action_msg)


    def real_damage_value(self, damage, target_defense):
        xx = min(0.024 * target_defense / (self.level + 9), 0.75)
        value = damage * (1 - xx)
        return value
        


    def normal_action(self, target, msg):
        target.active_property_effects()
        
        msg_target = msg.skill_targets.add()
        msg_target.target_id = target.id
        msg_target.is_dodge = False
        msg_target.is_crit = False
        if self.using_crit >= randint(1, 100):
            msg_target.is_crit = True
            
        if target.using_dodge >= randint(1, 100):
            msg_target.is_dodge = True
            
            
        text = "%d => %d, Crit: %s, Dodge: %s" % (
                self.id,
                target.id,
                msg_target.is_crit,
                msg_target.is_dodge
                )
        
        logger.debug(text)

        if  msg_target.is_dodge:
            return
        
        value = self.using_attack
        if msg_target.is_crit:
            value *= 2
        
        self._one_action(target, value, msg)


    def _one_action(self, target, value, msg, eff=None):
        # FIXME
        if not eff or eff == 2:
            value = self.real_damage_value(value, target.using_defense)

        hero_noti = msg.hero_notify.add()
        hero_noti.target_id = target.id

        value = int(value)
    
        target.set_hp(value)

        hero_noti.hp = target.hp
        hero_noti.value = value

        if eff:
            hero_noti.eff = eff
            
        text = 'Value: %d, Hp: %d, Eff: %s' % (
                value,
                target.hp,
                str(eff) if eff else 'None'
                )
        logger.debug(text)



    def effect_on(self, eff, target, msg, surely_hit=False):
        msg_target = msg.skill_targets.add()
        msg_target.target_id = target.id
        msg_target.is_dodge = False
        msg_target.is_crit = False
        if self.using_crit >= randint(1, 100):
            msg_target.is_crit = True

        target.active_property_effects()
        if target not in self._team:
            # 敌人
            if not surely_hit:
                if target.using_dodge >= randint(1, 100):
                    msg_target.is_dodge = True
                
        text = "%d => %d, Crit: %s, Dodge: %s" % (
                self.id,
                target.id,
                msg_target.is_crit,
                msg_target.is_dodge
                )
        
        logger.debug(text)
        
        if msg_target.is_dodge:
            return


        if eff.rounds == 0:
            if eff.type_id == 1:
                value = self._cal_eff_value(eff, target, 'hp')
                if msg_target.is_crit:
                    value *= 2
                self._one_action(target, -value, msg, 1)
            elif eff.type_id == 2:
                value = self._cal_eff_value(eff, self, 'using_attack')
                if msg_target.is_crit:
                    value *= 2
                self._one_action(target, value, msg, 2)
            elif eff.type_id == 12:
                raise NotImplementedError("eff.type_id = 12")
            #elif eff.type_id == 13:
            #    value = self._cal_eff_value(eff, self, 'using_attack')
            #    if msg_target.is_crit:
            #        value *= 2
            #    value -= target.using_defense
            #    if value < 0:
            #        value = 0
            #    self._one_action(target, value, msg, 13)
            #    self._one_action(self, -value, msg, 13)
            else:
                raise Exception("eff.rounds = 0, but type_id = %d" % eff.type_id)
        else:
            self.effect_manager.add_effect_to_target(target, eff, msg)
            
        return True


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
        
        effects = []
        for group_effs in skill.effects:
            new_group_effs = [eff.copy() for eff in group_effs]
            effects.append(new_group_effs)
        
        def _group_effs_action(effs):
            head_eff = effs[0]
            rest_eff = effs[1:]
            
            # 只要同一组中，第一个效果命中，同组的其他效果全部命中
            head_targets = self.get_effect_target(head_eff, target)
            hit = False
            for t in head_targets:
                hit = self.effect_on(head_eff, t, msg)
            
            for eff in rest_eff:
                targets = self.get_effect_target(eff, target)
                for t in targets:
                    self.effect_on(eff, t, msg, hit)
            
        
        for group_eff in effects:
            _group_effs_action(group_eff)
        


class BattleHero(InBattleHero):
    _hero_type = 1
    def __init__(self, _id):
        hero = get_cache_hero(_id)
        self.id = _id
        self.original_id = hero.oid
        self.attack = hero.attack
        self.defense = hero.defense
        self.hp = hero.hp
        self.crit = hero.crit
        self.dodge = hero.dodge
        
        self.skills = GLOBAL.HEROS[self.original_id]['skills']
        
        char = get_cache_character(hero.char_id)
        self.level = char.level
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
        self.level = info['level']

        InBattleHero.__init__(self)

