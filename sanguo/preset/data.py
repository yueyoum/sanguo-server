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


# def name_maker(fixture_file):
#     name = os.path.basename(fixture_file)
#     a, _ = os.path.splitext(name)
#     return a.upper()
#
# _globals = globals()
# for f in FIXTURES_FILES:
#     _globals[name_maker(f)] = object_maker(f)
#

def _find_file(fixture_name):
    for f in FIXTURES_FILES:
        if f.endswith(fixture_name):
            return f

    raise Exception("Can not find {0}".format(fixture_name))

FUNCTION_OPEN = object_maker(_find_file('function_open.json'))
CHARINIT = object_maker(_find_file('charinit.json'))[1]
ARENA_REWARD = object_maker(_find_file('arena_reward.json'))
SERVERS = object_maker(_find_file('servers.json'))
ACHIEVEMENTS = object_maker(_find_file('achievements.json'))
OFFICIAL = object_maker(_find_file('official.json'))
HEROS = object_maker(_find_file('heros.json'))
MONSTERS = object_maker(_find_file('monsters.json'))
STUFFS = object_maker(_find_file('stuffs.json'))
GEMS = object_maker(_find_file('gems.json'))
EQUIPMENTS = object_maker(_find_file('equipments.json'))
BATTLES = object_maker(_find_file('battles.json'))
STAGES = object_maker(_find_file('stages.json'))
STAGE_ELITE = object_maker(_find_file('stage_elite.json'))
STAGE_CHALLENGE = object_maker(_find_file('stage_challenge.json'))
STAGE_DROP = object_maker(_find_file('stage_drop.json'))
EFFECTS = object_maker(_find_file('effects.json'))
SKILLS = object_maker(_find_file('skills.json'))
SKILL_EFFECT = object_maker(_find_file('skill_effect.json'))
TASKS = object_maker(_find_file('tasks.json'))


for k, v in FUNCTION_OPEN.items():
    if v.char_level == 0 and v.stage_id == 0:
        FUNCTION_OPEN.pop(k)


def _parse_char_init():
    decoded_heros = {}
    for hero in CHARINIT.heros.split('|'):
        hero_id, equips = hero.split(':')
        equip_ids = [int(i) for i in equips.split(',')]
        decoded_heros[int(hero_id)] = equip_ids
    CHARINIT.decoded_heros = decoded_heros

    decoded_gems = []
    for gems in CHARINIT.gems.split(','):
        gid, amount = gems.split(':')
        decoded_gems.append((int(gid), int(amount)))
    CHARINIT.decoded_gems = decoded_gems

    decoded_stuffs = []
    for stuff in CHARINIT.stuffs.split(','):
        sid, amount = stuff.split(':')
        decoded_stuffs.append((int(sid), int(amount)))
    CHARINIT.decoded_stuffs = decoded_stuffs

_parse_char_init()



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

#
# EQUIPMENTS_INITIAL = {}
# for d in EQUIPMENTS.values():
#     if d.step == 0:
#         EQUIPMENTS_INITIAL[d.id] = d
#
#
#
#



STAGE_ELITE_CONDITION = {}
for k, v in STAGE_ELITE.iteritems():
    STAGE_ELITE_CONDITION.setdefault(v.open_condition, []).append(k)

TREASURES = {}
for d in STUFFS.values():
    if d.tp == 2:
        TREASURES[d.id] = d


class UsingEffect(object):
    __slots__ = ['id', 'target', 'value', 'rounds']
    def __init__(self, id, target, value, rounds):
        self.id = id
        self.target = target
        self.value = value
        self.rounds =  rounds

    def copy(self):
        return UsingEffect(self.id, self.target, self.value, self.rounds)


def _get_skill_effects(sid):
    res = []
    for se in SKILL_EFFECT.values():
        if se.skill == sid:
            res.append(UsingEffect(se.effect, se.target, se.value, se.rounds))
    return res

for s in SKILLS.values():
    s.effects = _get_skill_effects(s.id)


def _achievement_decoded_condition_values(self):
    if self.mode == 1:
        return [int(i) for i in self.condition_value.split(',')]
    return int(self.condition_value)

ACHIEVEMENT_CONDITIONS = {}
ACHIEVEMENT_FIRST_IDS = []
for ach in ACHIEVEMENTS.values():
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




TASKS_ALL_TP = []
for k, v in TASKS.iteritems():
    if v.tp not in TASKS_ALL_TP:
        TASKS_ALL_TP.append(v.tp)

TASKS_FIRST_IDS = []
for k, v in TASKS.iteritems():
    if v.first:
        TASKS_FIRST_IDS.append(k)


