# -*- coding: utf-8 -*-

"""
Skill
    MODE = (
            (1, "主动"), (2, "防御"),
            (3, "被动"),
            )

Effect
    TARGET = (
            (1, "敌单体"), (2, "自身"),
            (3, "敌全体"), (4, "己全体"),
            )

    TYPE = (
            (1, "加血"),
            (2, "伤害"),
            (3, "增加攻击"),
            (4, "降低攻击"),
            (5, "增加防御"),
            (6, "降低防御"),
            (7, "增加闪避"),
            (8, "降低闪避"),
            (9, "增加暴击"),
            (10, "降低暴击"),
            (11, "击晕"),
            (12, "反伤"),
            (13, "吸血"),
            (14, "生命上限")
            )
"""




class Effect(object):
    __slots__ = ['group_id', 'target', 'type_id', 'value', 'rounds', 'is_percent']
    def __init__(self, group_id, target, type_id, value, is_percent, rounds):
        self.group_id = group_id
        self.target = target
        self.type_id = type_id
        self.value = value
        self.is_percent = is_percent
        self.rounds = rounds


    def copy(self):
        return Effect(
                self.group_id,
                self.target,
                self.type_id,
                self.value,
                self.is_percent,
                self.rounds
                )



class Skill(object):
    __slots__ = ['id', 'mode', 'trig_prob', 'effects']
    def __init__(self, sid, mode, trig_prob, effects):
        self.id = sid
        self.mode = mode
        self.trig_prob = trig_prob
        self.effects = effects

