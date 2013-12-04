from core import GLOBAL
from core.drives import document_ids
from core.mongoscheme import MongoHero
from apps.character.cache import get_cache_character


def cal_hero_property(original_id, level):
    attack = 20 + level * GLOBAL.HEROS[original_id]['attack_grow']
    defense = 15 + level * GLOBAL.HEROS[original_id]['defense_grow']
    hp = 45 + level * GLOBAL.HEROS[original_id]['hp_grow']

    return attack, defense, hp



class Hero(object):
    def __init__(self, hid, original_id, level, char_id, skills):
        self.id = hid
        self.original_id = original_id
        self.level = level
        self.char_id = char_id
        self.skills = skills

        self.attack, self.defense, self.hp = \
                cal_hero_property(self.original_id, self.level)

        self.crit = 0
        self.dodge = 0

        self.additional_attributes()

    def additional_attributes(self):
        pass



def save_hero(char_id, hero_original_ids, add_notify=True):
    if not isinstance(hero_original_ids, (list, tuple)):
        hero_original_ids = [hero_original_ids]
    
    length = len(hero_original_ids)
    new_max_id = document_ids.inc('charhero', length)
    
    id_range = range(new_max_id-length+1, new_max_id+1)
    for i, _id in enumerate(id_range):
        MongoHero(id=_id, char=char_id, oid=hero_original_ids[i]).save()

    print "id_range =", id_range
    
    if add_notify:
        from core.notify import add_hero_notify
        from core.cache import get_cache_hero
        heros = [get_cache_hero(hid) for hid in id_range]
        add_hero_notify('noti:{0}'.format(char_id), heros)
    
    return id_range


def get_hero(_id):
    hero = MongoHero.objects.get(id=_id)
    original_id = hero.oid
    char_obj = get_cache_character(hero.char)
    return _id, original_id, char_obj.level, hero.char

def get_hero_obj(_id):
    _, oid, level, char_id = get_hero(_id)
    return Hero(_id, oid, level, char_id, [])


def delete_hero(_id):
    MongoHero.objects(id=_id).delete()
