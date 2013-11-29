import random
from collections import defaultdict

from core.mongoscheme import MongoChar
from apps.character.cache import get_cache_character
from core.signals import pve_finished_signal
from core.equip import generate_and_save_equip
from core import GLOBAL
from core.character import model_character_change

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
    model_character_change(char_id, exp=exp, gold=gold)
    
    # FIXME bulk create
    for tid, level, amount in equips:
        for i in range(amount):
            generate_and_save_equip(tid, level, char_id)
    
    # TODO gems
    


def _pve_finished(sender, char_id, stage_id, win, star, **kwargs):
    print "_pve_finished", char_id, stage_id, win, star
    from core.notify import current_stage_notify, new_stage_notify
    cache_char = get_cache_character(char_id)
    notify_key = cache_char.notify_key
    
    current_stage_notify(notify_key, stage_id, star)
    
    char = MongoChar.objects.only('stages').get(id=char_id)
    stages = char.stages
    if win:
        # FIXME
        new_stage_id = stage_id + 1
        char.stage_new = new_stage_id
        
        if str(new_stage_id) not in stages.keys():
            new_stage_notify(notify_key, new_stage_id)
            char.stages[str(stage_id)] = star
        
        char.save()
        


pve_finished_signal.connect(
    _pve_finished,
    dispatch_uid = 'core.stage._pve_finished'
)