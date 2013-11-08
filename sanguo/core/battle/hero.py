import logging
from random import randint
from core.hero import Hero
from core import GLOBAL

logger = logging.getLogger('battle')

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

        text = '%s. Target Buffs: %s' % (
                text,
                str(target.current_buff_list())
                )

        logger.debug(text)
        return msg_target, hero_notify
    return deco


class BattleMixIn(object):
    def __str__(self):
        return '<%d, %d>' % (self.id, self.original_id)


    def cal_fighting_power(self):
        return 100

    def current_buff_list(self):
        return [eff.type_id for eff in self.effects]

    def remove_outdated_effects(self):
        x = []

        for eff in self.effects[:]:
            eff.rounds -= 1
            if eff.rounds == 0:
                self.effects.remove(eff)
                x.append(eff.type_id)

        logger.debug("%d: remove effs %s, current effs %s" % (
            self.id, str(x), str(self.current_buff_list())))



    def using_effects(self):
        self.using_attack = self.attack
        self.using_defense = self.defense
        self.using_crit = self.crit
        self.using_dodge = self.dodge

        for eff in self.effects:
            if eff.type_id == 3:
                self.using_attack += int( eff.value / 100.0 * self.using_attack )
            elif eff.type_id == 4:
                self.using_attack -= int( eff.value / 100.0 * self.using_attack )
            elif eff.type_id == 5:
                self.using_defense += int( eff.value / 100.0 * self.using_defense )
            elif eff.type_id == 6:
                self.using_defense -= int( eff.value / 100.0 * self.using_defense )
            elif eff.type_id == 7:
                self.using_dodge += int( eff.value / 100.0 * self.using_dodge )
            elif eff.type_id == 8:
                self.using_dodge -= int( eff.value / 100.0 * self.using_dodge )
            elif eff.type_id == 9:
                self.using_crit += int( eff.value / 100.0 * self.using_crit )
            elif eff.type_id == 10:
                self.using_crit -= int( eff.value / 100.0 * self.using_crit )


    def find_prob(self, skills, base=70):
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
        if self.die:
            logger.debug("%d: die, return" % self.id)
            return

        msg = self.ground_msg.actions.add()
        msg.from_id = self.id

        self.using_effects()
        self.remove_outdated_effects()
        
        hero_notify = msg.hero_notify.add()
        hero_notify.target_id = self.id
        hero_notify.hp = self.hp
        hero_notify.buffs.extend(self.current_buff_list())

        for eff in self.effects:
            if eff.type_id == 11:
                logger.debug("%d: dizziness, return" % self.id)
                return

        skill = self.find_prob(self.attack_skills)

        if skill is None:
            logger.debug("%d: normal action" % self.id)
            self.normal_action(target, msg)
        else:
            logger.debug("%d: skill action %d" % (self.id, skill.id))
            self.skill_action(target, skill, msg)


    def normal_action(self, target, msg):
        self._one_action(target, self.using_attack, msg)


    @_logger_one_action
    def _one_action(self, target, damage, msg, eff=None):

        msg_target = msg.skill_targets.add()
        msg_target.target_id = target.id
        if self.using_crit >= randint(1, 100):
            damage *= 2
            msg_target.is_crit = True
        else:
            msg_target.is_crit = False

        target.using_effects()
        if target.using_dodge >= randint(1, 100):
            msg_target.is_dodge = True
            return msg_target, None

        msg_target.is_dodge = False
        hero_notify = msg.hero_notify.add()
        hero_notify.target_id = target.id

        damage -= target.using_defense
        if damage < 0:
            damage = 0
        else:
            target.hp -= damage
            if target.hp <= 0:
                target.hp = 0
                target.die = True

        hero_notify.hp = target.hp
        hero_notify.value = damage

        if eff:
            hero_notify.eff = eff

        return msg_target, hero_notify


        # target_defense_skill = self.find_prob(target.defense_skills)
        # if target_defense_skill is not None:
        #     self_target = _find_action_target_in_msg(msg, self.id)
        #     for eff in target_defense_skill.effects:
        #         if eff.type_id == 12:
        #             self_target.hp -= eff.value
        #             if self_target.hp < 0:
        #                 self_target.hp = 0
        #                 self_target.die = True
        #         else:
        #             effects = [eff.copy() for eff in target_defense_skill.effects]
        #             self.effects.extend(effects)
        #             effs = [eff.id for eff in effects]
        #             self_target.add_effs.extend(effs)



    def skill_action(self, target, skill, msg):
        msg.skill_id = skill.id
        effects = [eff.copy() for eff in skill.effects]

        for eff in effects:
            if eff.type_id == 2:
                continue

            if eff.target == 1 or eff.target == 2:
                eff_target = [target]
            elif eff.target == 3:
                eff_target = [t for t in target._team if t is not None]
            else:
                eff_target = [t for t in self._team if t is not None]

            for t in eff_target:
                hero_notify = msg.hero_notify.add()
                hero_notify.target_id = t.id
                hero_notify.hp = t.hp
                hero_notify.eff = eff.type_id
                hero_notify.buffs.extend(t.current_buff_list())


        damage_eff = None
        for eff in effects:
            if eff.type_id == 2:
                damage_eff = eff
                break

        if damage_eff is not None:
            if damage_eff.target == 1:
                damage_target = [target]
            elif damage_eff.target == 3:
                damage_target = [t for t in target._team if t is not None]

            for t in damage_target:
                self._one_action(t, damage_eff.value * self.using_attack / 100, msg, 2)


        for eff in effects[:]:
            if eff.type_id in [1, 2, 12, 13]:
                effects.remove(eff)


        for eff in effects:
            if eff.target == 1:
                if not target.die:
                    target.effects.append(eff)
                    logger.debug("Target %d, add eff %d" % (target.id, eff.type_id))
            elif eff.target == 2:
                if not target.die:
                    self.effects.append(eff)
                    logger.debug("Target %d, add eff %d" % (target.id, eff.type_id))
            elif eff.target == 3:
                for _h in target._team:
                    if _h is None or _h.die:
                        continue
                    _h.effects.append(eff)
                    logger.debug("Target %d, add eff %d" % (_h.id, eff.type_id))
            elif eff.target == 4:
                for _h in self._team:
                    if _h is None or _h.die:
                        continue
                    _h.effects.append(eff)
                    logger.debug("Target %d, add eff %d" % (_h.id, eff.type_id))





class BattleHero(BattleMixIn, Hero):
    def __init__(self, *args, **kwargs):
        Hero.__init__(self, *args, **kwargs)

        self.die = False

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


        self.effects = []



class MonsterHero(BattleMixIn):
    def __init__(self, mid):
        info = GLOBAL.MONSTERS[mid]
        self.id = mid
        self.original_id = mid
        self.attack = info['attack']
        self.defense = info['defense']
        self.hp = info['hp']
        self.crit = info['crit']
        self.dodge = info['dodge']

        self.die = False

        self.skills = [GLOBAL.SKILLS[sid] for sid in info['skills']]
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


        self.effects = []

