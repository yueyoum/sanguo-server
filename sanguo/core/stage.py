# -*- coding: utf-8 -*-
import random
from collections import defaultdict

from core.mongoscheme import MongoChar, Hang
from core import GLOBAL
from core.character import Char
from core.item import Item

from utils import timezone
from utils.math import GAUSSIAN_TABLE

STAGE = GLOBAL.STAGE
STAGE_DROP = GLOBAL.STAGE_DROP
GEM = GLOBAL.GEM


def get_already_stage(char_id):
    stages = MongoChar.objects.only('stages').get(id=char_id).stages
    if not stages:
        return None
    return {int(k): v for k, v in stages.iteritems()}


def get_new_stage(char_id):
    stage_new = MongoChar.objects.only('stage_new').get(id=char_id).stage_new
    return stage_new


def get_stage_fixed_drop(stage_id):
    # FIXME
    #stage = STAGE[stage_id]
    #drop_group_id = stage['normal_drop']
    #drop_exp = stage['normal_exp']
    #drop_gold = stage['normal_gold']
    #
    #items_drop = STAGE_DROP[drop_group_id]
    #
    #equip_drop = items_drop.get(4, [])
    #gem_drop = items_drop.get(5, [])
    #
    #equips = []
    ## [(tid, level, amount)]
    #for tid, level, prob, min_amount, max_amount in equip_drop:
    #    # FIXME
    #    #if prob < random.randint(1, 100):
    #    #    continue
    #    
    #    amount = random.choice(range(min_amount, max_amount+1))
    #    equips.append(
    #        (tid, level, amount)
    #    )
    #
    #gems = defaultdict(lambda: 0)
    ## [(id, amount)]
    #for level, prob, min_amount, max_amount in gem_drop:
    #    # FIXME
    #    #if prob < random.randint(1, 100):
    #    #    continue
    #    
    #    amount = random.choice(range(min_amount, max_amount+1))
    #    this_level_ids = GEM.get_ids_by_level(level)
    #    
    #    for i in range(amount):
    #        _id = random.choice(this_level_ids)
    #        this_level_ids.remove(_id)
    #        gems[_id] += 1
    #
    #gems = gems.items()
    #
    #return drop_exp, drop_gold, equips, gems
    return 0, 0, [], []


def get_stage_standard_drop(char_id, stage_id, star=False):
    stage = STAGE[stage_id]
    stage_level = stage['level']

    drop_exp = stage['normal_exp']
    drop_gold = stage['normal_gold']

    mc = MongoChar.objects.only('stages').get(id=char_id)
    if str(stage_id) not in mc.stages:
        # 首通
        drop_exp += stage['first_exp']
        drop_gold += stage['first_gold']

    if star:
        # 三星
        drop_exp += stage['star_exp']
        drop_gold += stage['star_gold']


    def _drop(prob_list):
        prob = random.uniform(0, 1)
        for sign, p in prob_list:
            if prob < p:
                return sign

            prob -= p

        return None


    # FIXME
    k = 0.3
    gem_level_prob = (
        (1, 1 * 0.01 * k),
        (2, 0.1 * 0.01 * k),
        (3, 0.05 * 0.01 * k),
        (4, 0.025 * 0.01 * k),
        (5, 0.005 * 0.01 * k),
        (6, 0.001 * 0.01 * k),
    )

    gems = []
    drop_gem_level = _drop(gem_level_prob)
    if drop_gem_level:
        gems = [
            (
                random.choice(GEM.get_ids_by_level(drop_gem_level)),
                1
            )
        ]

    equip_k = k / 0.6
    equip_quality_prob = (
        (1, 20.0 / 4000 / equip_k),
        (2, 15.0 / 4000 * equip_k),
        (3, 4.0 / 4000 * equip_k),
        (4, 0.3 / 4000 * equip_k),
    )

    drop_equip_quality = _drop(equip_quality_prob)
    equips = []
    if drop_equip_quality:
        selected_equip_ids = []
        for k, v in GLOBAL.EQUIP.EQUIP_TEMPLATE.iteritems():
            if not v['std'] or v['quality'] != drop_equip_quality:
                continue

            selected_equip_ids.append(k)

        equips = [
            (random.choice(selected_equip_ids), stage_level, 1)
        ]

    return drop_exp, drop_gold, equips, gems


def save_drop(char_id, exp, gold, equips, gems):
    print "save drop:", exp, gold, equips, gems
    char = Char(char_id)
    char.update(exp=exp, gold=gold)

    # equips
    # FIXME bulk create
    for tid, level, amount in equips:
        for i in range(amount):
            # TODO drop equip
            pass
            # generate_and_save_equip(tid, level, char_id)

    # gems
    item = Item(char_id)
    item.gem_add(gems)


static_day_hours = 18
static_var = 0.25
static_gem = 65
static_g5 = 0.00005 * 0.5 * 240 * static_day_hours
static_g6 = 0.00001 * 0.5 * 240 * static_day_hours

static_e1 = 20
static_e2 = 15
static_e3 = 4
static_e4 = 0.3

static_z = 0.6

GEM_LEVEL_SCORE = [
    (1, 1), (2, 4), (3, 16), (4, 64),
]

GEM_LEVEL_SCORE.reverse()


def _gem_list(gem_score):
    gem_score = int(gem_score)
    res = []
    for level, score in GEM_LEVEL_SCORE:
        a, b = divmod(gem_score, score)
        if a:
            res.append((level, a))
        gem_score = b

    return res


def _prob_amount(prob):
    prob = int(prob)
    a, b = divmod(prob, 100)
    if b:
        if b > random.randint(1, 100):
            a += 1
    return a


def get_stage_hang_drop(stage_id, hours):
    stage = STAGE[stage_id]
    drop_exp = stage['normal_exp']
    drop_gold = stage['normal_gold']

    exp = drop_exp * hours * 240
    gold = drop_gold * hours * 240

    seed = random.uniform(0.5, 0.99)
    seed = round(seed, 2)
    value = GAUSSIAN_TABLE[seed]
    r = 1 + value * static_var
    # FIXME
    #k = stage['level']
    k = 0.3
    rk = r * k
    gem_actual = static_gem * rk * hours / static_day_hours

    gem_list = _gem_list(gem_actual)

    g5 = int(static_g5 * rk * 100)
    g6 = int(static_g6 * rk * 100)

    g5_amount = _prob_amount(g5)
    if g5_amount:
        gem_list.append((5, g5_amount))

    g6_amount = _prob_amount(g6)
    if g6_amount:
        gem_list.append((6, g6_amount))

    gems = defaultdict(lambda: 0)
    for glv, gamount in gem_list:
        gids = GEM.get_ids_by_level(glv)
        for i in range(gamount):
            _id = random.choice(gids)
            gems[_id] += 1

    gems = gems.items()

    e1 = static_e1 * k / static_z * r * hours / static_day_hours * 100
    e2 = static_e2 * k / static_z * r * hours / static_day_hours * 100
    e3 = static_e3 * k / static_z * r * hours / static_day_hours * 100
    e4 = static_e4 * static_z / k * r * hours / static_day_hours * 100

    equip_list = []
    equips = (
        (1, e1), (2, e2), (3, e3), (4, e4)
    )
    for quality, eprob in equips:
        amount = _prob_amount(eprob)
        if amount:
            equip_list.append((quality, amount))

    equips_dict = defaultdict(lambda: 0)
    for quality, amount in equip_list:
        eids = GLOBAL.EQUIP.EQUIP_IDS_BY_QUALITY(quality, only_std=True)
        for i in range(amount):
            _id = random.choice(eids)
            equips_dict[_id] += 1

    equips = []
    for k, v in equips_dict.iteritems():
        equips.append((k, stage_id, v))

    return exp, gold, equips, gems


def get_plunder_list(char_id):
    mongo_char = MongoChar.objects.only('stages').get(id=char_id)
    stages = mongo_char.stages

    # FIXME 高效的最后一个三星关卡找取
    stages_items = [int(k) for k, v in stages.iteritems() if v]
    stages_items.sort()

    def _find_hang(stage_id):
        hang_list = Hang.objects(stage_id=stage_id)
        stage_gold = GLOBAL.STAGE[stage_id]['normal_gold'] * 240
        res = []
        for h in hang_list:
            total_seconds = h.hours * 3600
            passed_seconds = timezone.utc_timestamp() - h.start
            if passed_seconds * 5 >= total_seconds:
                res.append((h.id, (stage_gold * h.hours / 5)))

        return res


    plunder_list = []
    if stages_items:
        this_stage_id = stages_items[-1]

        while True:
            if this_stage_id < 0:
                break
            plunder_list.extend(_find_hang(this_stage_id))

            if len(plunder_list) >= 10:
                break

        if len(plunder_list) >= 10:
            plunder_list = plunder_list[:10]

    return plunder_list
    

