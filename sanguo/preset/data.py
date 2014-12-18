# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '3/28/14'

import os
import glob
import json
import random

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURES_FILES = glob.glob(os.path.join(CURRENT_PATH, 'fixtures', '*.json'))


class Data(object):
    pass

def object_maker(fixture_file):
    with open(fixture_file, 'r') as f:
        content = json.loads(f.read())

    res = {}
    for c in content:
        d = Data()
        d.id = c['pk']
        for k, v in c['fields'].iteritems():
            setattr(d, k, v)

        res[d.id] = d

    return res

def _find_file(fixture_name):
    for f in FIXTURES_FILES:
        if f.endswith(fixture_name):
            return f

    raise Exception("Can not find {0}".format(fixture_name))

FUNCTION_DEFINE = object_maker(_find_file('function_define.json'))
ARENA_DAY_REWARD = object_maker(_find_file('arena_day_reward.json'))
ARENA_WEEK_REWARD = object_maker(_find_file('arena_week_reward.json'))
ACHIEVEMENTS = object_maker(_find_file('achievements.json'))
OFFICIAL = object_maker(_find_file('official.json'))
HEROS = object_maker(_find_file('heros.json'))
MONSTERS = object_maker(_find_file('monsters.json'))
STUFFS = object_maker(_find_file('stuffs.json'))
GEMS = object_maker(_find_file('gems.json'))
EQUIPMENTS = object_maker(_find_file('equipments.json'))
BATTLES = object_maker(_find_file('battles.json'))
STAGE_TYPE = object_maker(_find_file('stage_type.json'))
STAGES = object_maker(_find_file('stages.json'))
STAGE_ELITE = object_maker(_find_file('stage_elite.json'))
STAGE_ACTIVITY = object_maker(_find_file('stage_activity.json'))
STAGE_CHALLENGE = object_maker(_find_file('stage_challenge.json'))
EFFECTS = object_maker(_find_file('effects.json'))
SKILLS = object_maker(_find_file('skills.json'))
SKILL_EFFECT = object_maker(_find_file('skill_effect.json'))
TASKS = object_maker(_find_file('tasks.json'))
VIP_FUNCTION = object_maker(_find_file('vip.json'))
VIP_REWARD = object_maker(_find_file('vip_reward.json'))

ARENA_DAY_REWARD_TUPLE = ARENA_DAY_REWARD.items()
ARENA_DAY_REWARD_TUPLE.sort(key=lambda item: -item[0])


PURCHASE = object_maker(_find_file('purchase.json'))
PURCHASE_TYPE = object_maker(_find_file('purchase_type.json'))

ACTIVITY_STATIC = object_maker(_find_file('activity_static.json'))
ACTIVITY_STATIC_CONDITIONS = object_maker(_find_file('activity_static_condition.json'))

VALUE_SETTING = object_maker(_find_file('value_setting.json'))

HORSE = object_maker(_find_file('horse.json'))

UNION_STORE = object_maker(_find_file('union_store.json'))
UNION_CHECKIN = object_maker(_find_file('union_checkin.json'))
UNION_BOSS = object_maker(_find_file('union_boss.json'))
UNION_BOSS_REWARD = object_maker(_find_file('union_boss_reward.json'))
UNION_LEVEL = object_maker(_find_file('union_level.json'))
UNION_POSITION = object_maker(_find_file('union_position.json'))
UNION_BATTLE_REWARD = object_maker(_find_file('union_battle_reward.json'))

def _got_package():
    f = _find_file('package.json')
    with open(f, 'r') as x:
        data = json.loads(x.read())
    p = {}
    for k, v in data.iteritems():
        p[int(k)] = v
    return p

PACKAGES = _got_package()


for k, v in FUNCTION_DEFINE.items():
    if v.char_level == 0 and v.stage_id == 0:
        FUNCTION_DEFINE.pop(k)



def _hero_special_equipments(self):
    if not self.special_equip_cls:
        return {}
    equip_cls = [int(i) for i in self.special_equip_cls.split(',')]
    equip_addition = [int(i) for i in self.special_addition.split(',')]
    data = dict(zip(equip_cls, equip_addition))
    return data

for h in HEROS.values():
    h.special_equipments = _hero_special_equipments(h)


def HERO_GET_BY_QUALITY(quality, amount=1):
    all_heros = HEROS.values()
    res = {}
    while True:
        if not amount:
            if not all_heros:
                break
        else:
            if len(res) >= amount:
                break

        this = random.choice(all_heros)
        all_heros.remove(this)
        if this.id in res:
            continue
        if this.quality != quality:
            continue

        res[this.id] = this

    return res


def HERO_GET_BY_QUALITY_NOT_EQUAL(quality, amount=1):
    all_heros = HEROS.values()
    res = {}
    while True:
        if not amount:
            if not all_heros:
                break
        else:
            if len(res) >= amount:
                break

        this = random.choice(all_heros)
        all_heros.remove(this)
        if this.id in res:
            continue
        if this.quality == quality:
            continue

        res[this.id] = this

    return res

def HERO_GET_BY_GRADE(grade, amount=1):
    all_heros = HEROS.values()
    res = {}
    while True:
        if not amount:
            if not all_heros:
                break
        else:
            if len(res) >= amount:
                break

        this = random.choice(all_heros)
        if this.id in res:
            continue
        if this.grade != grade:
            continue

        res[this.id] = this

    return res

STAGE_ACTIVITY_CONDITION = {}
STAGE_ACTIVITY_TPS = []
for k, v in STAGE_ACTIVITY.iteritems():
    STAGE_ACTIVITY_CONDITION.setdefault(v.char_level, []).append(k)
    if v.tp not in STAGE_ACTIVITY_TPS:
        STAGE_ACTIVITY_TPS.append(v.tp)


STAGE_ELITE_FIRST_ID = sorted(STAGE_ELITE.keys())[0]
STAGE_ELITE_CONDITION = {}
for k, v in STAGE_ELITE.items():
    if getattr(v, 'previous', None) is None:
        setattr(v, 'previous', None)

    if v.next:
        STAGE_ELITE[v.next].previous = k

    STAGE_ELITE_CONDITION.setdefault(v.open_condition, []).append(v)

def _make_elite_in_chain(stages):
    stages_dict = {s.id: s for s in stages}
    stage_ids = [s.id for s in stages]

    def _find_first_stage():
        for s in stages:
            if not s.previous:
                return s

            if s.previous not in stage_ids:
                return s

    first_stage = _find_first_stage()
    re_sorted = [first_stage]
    while len(re_sorted) < len(stages):
        re_sorted.append(stages_dict[re_sorted[-1].next])

    return re_sorted

for k, v in STAGE_ELITE_CONDITION.items():
    STAGE_ELITE_CONDITION[k] = _make_elite_in_chain(v)



TREASURES = {}
for d in STUFFS.values():
    if d.tp == 2:
        TREASURES[d.id] = d


class UsingEffect(object):
    __slots__ = ['id', 'target', 'value', 'rounds', 'is_hit_target']
    def __init__(self, id, target, value, rounds, is_hit_target):
        self.id = id
        self.target = target
        self.value = value
        self.rounds =  rounds
        self.is_hit_target = is_hit_target

    def copy(self):
        return UsingEffect(self.id, self.target, self.value, self.rounds, self.is_hit_target)


def _get_skill_effects(sid):
    res = []
    for se in SKILL_EFFECT.values():
        if se.skill == sid:
            res.append(UsingEffect(se.effect, se.target, se.value, se.rounds, se.is_hit_target))
    return res

for s in SKILLS.values():
    s.effects = _get_skill_effects(s.id)


def _achievement_decoded_condition_values(self):
    if self.mode == 1:
        return [int(i) for i in self.condition_value.split(',')]
    return int(self.condition_value)

ACHIEVEMENT_CONDITIONS = {}
ACHIEVEMENT_FIRST_IDS = []
for aid, ach in ACHIEVEMENTS.items():
    if not ach.open:
        ACHIEVEMENTS.pop(aid)
        continue

    ach.decoded_condition_value = _achievement_decoded_condition_values(ach)
    ACHIEVEMENT_CONDITIONS.setdefault(ach.condition_id, []).append(ach)
    if ach.first:
        ACHIEVEMENT_FIRST_IDS.append(ach.id)


def _stage_decoded_monsters(self):
    return [int(i) for i in self.monsters.split(',')]


for s in STAGES.values():
    bid = s.battle
    s.level_limit = BATTLES[bid].level_limit
    s.decoded_monsters = _stage_decoded_monsters(s)
    open_condition = s.open_condition
    if open_condition:
        STAGES[open_condition].next = s.id

for s in STAGE_ELITE.values():
    s.decoded_monsters = _stage_decoded_monsters(s)

for s in STAGE_ACTIVITY.values():
    s.decoded_monsters = _stage_decoded_monsters(s)



TASKS_ALL_TP = []
for k, v in TASKS.iteritems():
    if v.tp not in TASKS_ALL_TP:
        TASKS_ALL_TP.append(v.tp)

TASKS_FIRST_IDS = []
for k, v in TASKS.iteritems():
    if v.first:
        TASKS_FIRST_IDS.append(k)


VIP_DEFINE = []
for k, v in VIP_FUNCTION.iteritems():
    VIP_DEFINE.append((v.sycee, k))
VIP_DEFINE.sort(key=lambda item: item[0])

_vip_levels = VIP_FUNCTION.keys()
_vip_levels.sort()

VIP_MAX_LEVEL = _vip_levels[-1]


# PURCHASE
for v in PURCHASE.values():
    v.tp_obj = PURCHASE_TYPE[v.tp]


# ACTIVITY
for v in ACTIVITY_STATIC.values():
    v.total_continued_hours = v.continued_days * 24 + v.continued_hours
    condition_ids = [int(i) for i in v.conditions.split(',')]

    condition_objs = []
    for i in condition_ids:
        _ac_con_obj = ACTIVITY_STATIC_CONDITIONS[i]
        _ac_con_obj.activity_id = v.id
        condition_objs.append(_ac_con_obj)

    v.condition_objs = condition_objs

