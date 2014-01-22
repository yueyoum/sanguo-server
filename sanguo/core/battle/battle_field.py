# -*- coding: utf-8 -*-
import logging
from collections import defaultdict

from mixins import ActiveEffectMixin

TARGET_RULE = {
    0: [0, 1, 2],
    1: [1, 0, 2],
    2: [2, 1, 0],
}

logger = logging.getLogger('battle')


class HeapEffects(object):
    def __init__(self):
        self.x = defaultdict(lambda: [])

    def __str__(self):
        x = {}
        for k, v in self.x.iteritems():
            x[k.id] = [(_v.id, _v.value) for _v in v]
        return str(x)

    def add(self, h, eff):
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

        passive_skills = self.active_passive_effects()

        for h, effs in passive_skills.items():
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


    def active_passive_effects(self):
        # 被动技能的效果叠加
        heap_effect = HeapEffects()

        def _active_all(team_one, team_two):
            for h in team_one:
                if h is None:
                    continue

                for sk in h.passive_skills:
                    for eff in sk.effects:
                        if eff.target == 1:
                            raise Exception("UnSupported Passive Skill Effect, Target: 1")
                        if eff.target == 2:
                            heap_effect.add(h, eff)
                        elif eff.target == 3:
                            for h in team_two:
                                if h:
                                    heap_effect.add(h, eff)
                        elif eff.target == 4:
                            for h in team_one:
                                if h:
                                    heap_effect.add(h, eff)


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


