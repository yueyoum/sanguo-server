# -*- coding: utf-8 -*-

from core.mongoscheme import MongoChar, MongoHero
from core import GLOBAL
from core.hero import save_hero
from core.formation import save_socket, save_formation
from core.hero import Hero
from apps.character.cache import get_cache_character
from apps.character.models import Character
from apps.item.cache import get_cache_equipment

from core.cache import get_cache_hero

def char_initialize(account_id, server_id, name):
    # 随机三个武将，并上阵
    char = Character.objects.create(
        account_id = account_id,
        server_id = server_id,
        name = name
    )
    char_id = char.id
    
    MongoChar(id=char_id).save()
    
    init_hero_ids = GLOBAL.HEROS.get_random_hero_ids(3)
    
    hero_ids = save_hero(char_id, init_hero_ids)
    for index, _id in enumerate(hero_ids):
        save_socket(char_id, socket_id=index+1, hero=_id)

    socket_ids = [
            1, 0, 0,
            2, 0, 0,
            3, 0, 0,
            ]

    save_formation(char_id, socket_ids)


    # 将关卡1设置为new 可进入
    MongoChar.objects(id=char_id).update_one(set__stage_new=1)
    
    # FIXME just for test
    #import random
    #from core.equip import generate_and_save_equip
    #for i in range(10):
    #    generate_and_save_equip(
    #        random.randint(1, 12),
    #        random.randint(1, 99),
    #        char_id
    #    )
   # TEST END
    return char

def get_char_formation(char_id):
    char = MongoChar.objects.only('formation').get(id=char_id)
    return char.formation



def get_char_heros(char_id):
    heros = MongoHero.objects(char=char_id)
    return {h.id: h.oid for h in heros}
    
def get_char_hero_objs(char_id):
    data = get_char_heros(char_id)
    return [get_cache_hero(k) for k in data.keys()]
    #char_obj = get_cache_character(char_id)
    #return [Hero(k, v, char_obj.level, []) for k, v in data.iteritems()]
    

def get_char_equipments(char_id):
    char = MongoChar.objects.only('equips').get(id=char_id)
    return char.equips

def get_char_equipment_objs(char_id):
    equip_ids = get_char_equipments(char_id)
    objs = [get_cache_equipment(eid) for eid in equip_ids]
    return objs



def model_character_change(char_id, exp=0, honor=0, gold=0, gem=0):
    from core.notify import character_notify
    char = Character.objects.get(id=char_id)
    char.gold += gold
    char.honor += honor
    
    if exp:
        new_exp = char.exp + exp
        level, _, _ = GLOBAL.LEVEL_TOTALEXP[new_exp]
        char.level = level
        char.exp = new_exp
        
    # TODO honor
    char.save()
    
    notify_key = char.notify_key
    character_notify(notify_key, char)
    
