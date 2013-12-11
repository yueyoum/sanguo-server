# -*- coding: utf-8 -*-
import random
from collections import defaultdict

from core.mongoscheme import MongoChar, Hang
from core.equip import generate_and_save_equip
from core.gem import save_gem
from core import GLOBAL
from core.character import character_change

from apps.character.cache import get_cache_character

from utils import timezone

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


def get_stage_drop(char_id, stage_id):
    # FIXME
    stage = STAGE[stage_id]
    drop_group_id = stage['normal_drop']
    drop_exp = stage['normal_exp']
    drop_gold = stage['normal_gold']
    
    items_drop = STAGE_DROP[drop_group_id]
    
    equip_drop = items_drop.get(4, [])
    gem_drop = items_drop.get(5, [])
    
    equips = []
    # [(tid, level, amount)]
    for tid, level, prob, min_amount, max_amount in equip_drop:
        # FIXME
        #if prob < random.randint(1, 100):
        #    continue
        
        amount = random.choice(range(min_amount, max_amount+1))
        equips.append(
            (tid, level, amount)
        )
    
    gems = defaultdict(lambda: 0)
    # [(id, amount)]
    for level, prob, min_amount, max_amount in gem_drop:
        # FIXME
        #if prob < random.randint(1, 100):
        #    continue
        
        amount = random.choice(range(min_amount, max_amount+1))
        this_level_ids = GEM.get_ids_by_level(level)
        
        for i in range(amount):
            _id = random.choice(this_level_ids)
            this_level_ids.remove(_id)
            gems[_id] += 1
    
    gems = gems.items()
    
    
    save_drop(char_id, drop_exp, drop_gold, equips, gems)
    return drop_exp, drop_gold, equips, gems
    


def save_drop(char_id, exp, gold, equips, gems):
    print "save drop:", exp, gold, equips, gems
    character_change(char_id, exp=exp, gold=gold)
    
    # equips
    # FIXME bulk create
    for tid, level, amount in equips:
        for i in range(amount):
            generate_and_save_equip(tid, level, char_id)
    
    # gems
    save_gem(gems, char_id)
    

def get_npc_list(level, amount):
    return []


def get_plunder_list(char_id):
    mongo_char = MongoChar.objects.only('stages').get(id=char_id)
    stages = mongo_char.stages
    
    # FIXME 高效的最后一个三星关卡找取
    stages_items = [int(k) for k, v in stages.iteritems() if v]
    stages_items.sort()
    
    def _find_hang(stage_id):
        hang_list = Hang.objects(stage_id=stage_id)
        res = []
        for h in hang_list:
            total_seconds = h.hours * 3600
            passed_seconds = timezone.utc_timestamp() - h.start
            if passed_seconds * 5 >= total_seconds:
                res.append((h.id, False, h.hours))
        
        return res
        
    
    plunder_list = []
    needs_npc_amount = 0
    if not stages_items:
        print "get npc"
        needs_npc_amount = 10
    else:
        max_star_stage_id = stages_items[-1]
        
        for i in range(5):
            this_stage_id = max_star_stage_id - i
            plunder_list.extend(_find_hang(this_stage_id))
            
            if len(plunder_list) >= 10:
                break
        
        if len(plunder_list) >= 10:
            plunder_list = plunder_list[:10]
        else:
            needs_npc_amount = 10 - len(plunder_list)
    
    cache_char = get_cache_character(char_id)
    if needs_npc_amount:
        npcs = get_npc_list(cache_char.level, needs_npc_amount)
        plunder_list.extend(npcs)
    
    return plunder_list
    

