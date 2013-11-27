# -*- coding: utf-8 -*-

#from core.drives import document_char, document_stage
from core.mongoscheme import MongoChar, MongoHero
from core import GLOBAL
from core.hero import save_hero
from core.formation import save_socket, save_formation
from core.hero import Hero
from apps.character.cache import get_cache_character
from apps.character.models import Character

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
    #document_stage.set(char_id, new=1)
    MongoChar.objects(id=char_id).update_one(set__stage_new=1)
    return char

def get_char_formation(char_id):
    #char_formation = document_char.get(char_id, formation=1)
    char = MongoChar.objects.only('formation').get(id=char_id)
    return char.formation
    #return char_formation['formation']



def get_char_heros(char_id):
    #data = document_char.get(char_id, hero=1)
    heros = MongoHero.objects(char=char_id)
    return {h.id: h.oid for h in heros}
    
def get_char_hero_objs(char_id):
    data = get_char_heros(char_id)
    char_obj = get_cache_character(char_id)
    return [Hero(k, v, char_obj.level, []) for k, v in data.iteritems()]
    
