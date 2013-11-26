from core import GLOBAL
from core.drives import document_ids, document_char, document_hero
from apps.character.cache import get_cache_character


def cal_hero_property(original_id, level):
    attack = 20 + level * GLOBAL.HEROS[original_id]['attack_grow']
    defense = 15 + level * GLOBAL.HEROS[original_id]['defense_grow']
    hp = 45 + level * GLOBAL.HEROS[original_id]['hp_grow']

    return attack, defense, hp



class Hero(object):
    def __init__(self, hid, original_id, level, skills):
        self.id = hid
        self.original_id = original_id
        self.level = level
        self.skills = skills

        self.attack, self.defense, self.hp = \
                cal_hero_property(self.original_id, self.level)

        self.crit = 20
        self.dodge = 20

        self.additional_attributes()

    def additional_attributes(self):
        pass



def save_hero(char_id, hero_original_ids):
    if not isinstance(hero_original_ids, (list, tuple)):
        hero_original_ids = [hero_original_ids]
    
    length = len(hero_original_ids)
    new_max_id = document_ids.inc('charhero', length)
    
    id_range = range(new_max_id-length+1, new_max_id+1)
    data = {}
    for i, _id in enumerate(id_range):
        document_hero.set(_id, char=char_id)
        data['hero.%d' % _id] = hero_original_ids[i]

    document_char.set(char_id, **data)
    print "id_range =", id_range
    return id_range


def get_hero(_id, char_id=None):
    if not char_id:
        char_id = document_hero.get(_id)['char']
    original_id = document_char.get(char_id, hero=1)['hero'][str(_id)]
    char_obj = get_cache_character(char_id)
    return _id, original_id, char_obj.level



def delete_hero(_id, char_id=None):
    if not char_id:
        char_id = document_hero.get(_id)['char_id']
    document_hero.remove(_id)
    document_char.unset(char_id, 'hero.%d' % _id)
    
