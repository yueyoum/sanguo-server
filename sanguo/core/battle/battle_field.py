# -*- coding: utf-8 -*-
import logging
import random
from collections import defaultdict

from mixins import ActiveEffectMixin, StepHeroNotifyMixin

TARGET_RULE = {
    0: [0, 1, 2],
    1: [1, 0, 2],
    2: [2, 1, 0],
}

logger = logging.getLogger('battle')



class HeapEffects(StepHeroNotifyMixin):
    def __init__(self):
        self.x = defaultdict(lambda: [])

    def __str__(self):
        x = {}
        for k, v in self.x.iteritems():
            x[k.id] = [(_v.id, _v.value) for _v in v]
        return str(x)

    def add(self, h, eff, step_msg):
        target = step_msg.action.targets.add()
        target.target_id = h.id
        target.is_crit = False

        self.fill_up_heor_notify(step_msg, h, eff)

        eff = eff.copy()
        effs = self.x[h]
        _same = False
        for e in effs:
            if e.id == eff.id:
                e.value += eff.value
                _same = True
                break

        if not _same:
            self.x[h].append(eff)

    def items(self):
        return self.x.items()



class BattleField(ActiveEffectMixin):
    __slots__ = ['team_one', 'team_two', 'current_pos', 'msg']

    def __init__(self, team_one, team_two, msg):
        self.team_one = team_one
        self.team_two = team_two

        passive_skills_effs = self.active_passive_effects(msg)

        for h, effs in passive_skills_effs.items():
            for e in effs:
                self.active_effect(h, e, using_attr=False)



        for index, h in enumerate(self.team_one):
            if h is not None:
                h._index = index
                h._team = self.team_one
                h.ground_msg = msg
                logger.debug(
                    "{0}: Attack {1}, Defense {2}, Hp {3}, Crit {4}".format(
                        h.id, h.attack, h.defense, h.hp, h.crit
                    )
                )

        for index, h in enumerate(self.team_two):
            if h is not None:
                h._index = index
                h._team = self.team_two
                h.ground_msg = msg
                logger.debug(
                    "{0}: Attack {1}, Defense {2}, Hp {3}, Crit {4}".format(
                        h.id, h.attack, h.defense, h.hp, h.crit
                    )
                )

        self.current_pos = 0


    def active_passive_effects(self, msg):
        # 被动技能的效果叠加
        heap_effect = HeapEffects()

        def _active_all(team_one, team_two):
            for me in team_one:
                if me is None:
                    continue

                for sk in me.passive_skills:

                    step = msg.steps.add()
                    step.id = me.id

                    step.action.skill_id = sk.id

                    for eff in sk.effects:
                        if eff.target == 1:
                            # 敌单体
                            raise Exception("Active Passive Skill: UnSupported Passive Skill Effect, Target: 1")
                        if eff.target == 2:
                            # 自己
                            heap_effect.add(me, eff, step)
                        elif eff.target == 3:
                            # 敌全体
                            for h in team_two:
                                if h:
                                    heap_effect.add(h, eff, step)
                        elif eff.target == 4:
                            # 已全体
                            for h in team_one:
                                if h:
                                    heap_effect.add(h, eff, step)
                        elif eff.target == 5:
                            # 敌随机一个
                            team = []
                            for h in team_two:
                                if h:
                                    team.append(h)
                            if not team:
                                raise Exception("Active Passive Skill: No Target. Target: 5")

                            h = random.choice(team)
                            heap_effect.add(h, eff, step)
                        elif eff.target == 6:
                            # 敌随机两个
                            team = []
                            for h in team_two:
                                if h:
                                    team.append(h)
                            if not team:
                                raise Exception("Active Passive Skill: No Target. Target: 6")

                            if len(team) <= 2:
                                for h in team:
                                    heap_effect.add(h, eff, step)
                            else:
                                for i in range(2):
                                    h = random.choice(team)
                                    team.remove(h)
                                    heap_effect.add(h, eff, step)
                        elif eff.target == 7:
                            # 己随机一个
                            team = []
                            for h in team_one:
                                if h:
                                    team.append(h)
                            if not team:
                                raise Exception("Active Passive Skill: No Target. Target: 7")

                            h = random.choice(team)
                            heap_effect.add(h, eff, step)
                        elif eff.target == 8:
                            # 已随机两个
                            team = []
                            for h in team_one:
                                if h:
                                    team.append(h)
                            if not team:
                                raise Exception("Active Passive Skill: No Target. Target: 8")

                            if len(team) <= 2:
                                for h in team:
                                    heap_effect.add(h, eff, step)
                            else:
                                for i in range(2):
                                    h = random.choice(team)
                                    team.remove(h)
                                    heap_effect.add(h, eff, step)


        _active_all(self.team_one, self.team_two)
        _active_all(self.team_two, self.team_one)

        logger.debug("Active Passive Effects: %s" % str(heap_effect))
        return heap_effect


    def change_current_pos(self):
        self.current_pos += 1
        if self.current_pos >= 3:
            self.current_pos = 0

    def action(self):
        hero_pairs = self.find_hero_pairs()

        _p = []
        for a, b in hero_pairs:
            _p.append((a.id, b.id))
        logger.debug(str(_p))

        for a, b in hero_pairs:
            a.action(b)


    def find_hero_pairs(self):
        while True:
            hero = self.team_one[self.current_pos]
            opposite = self.team_two[self.current_pos]
            if hero is None or hero.die:
                if opposite is None or opposite.die:
                    self.change_current_pos()
                    continue

                hero = self.choose_target(self.team_one, self.current_pos)
                self.change_current_pos()
                return ((opposite, hero),)

            if opposite is None or opposite.die:
                target = self.choose_target(self.team_two, self.current_pos)
                self.change_current_pos()
                return ((hero, target),)

            self.change_current_pos()
            return ((hero, opposite), (opposite, hero),)


    def choose_target(self, base, index):
        for pos in TARGET_RULE[index]:
            h = base[pos]
            if h is None or h.die:
                continue

            return h

        raise Exception("choose_target error")


