from redisco import models
from core.signals import socket_changed_signal
from apps.item.cache import get_cache_equipment
from apps.character.cache import get_cache_character

from core.mongoscheme import MongoChar



class CacheHero(models.Model):
    char_id = models.IntegerField(indexed=False, required=True)
    oid = models.IntegerField(indexed=False, required=True)
    attack = models.IntegerField(indexed=False, required=True)
    defense = models.IntegerField(indexed=False, required=True)
    hp = models.IntegerField(indexed=False, required=True)
    crit = models.IntegerField(indexed=False, required=True)
    dodge = models.IntegerField(indexed=False, required=True)
    

def save_cache_hero(hero_obj):
    h = CacheHero.objects.get_by_id(hero_obj.id)
    if h is None:
        h = CacheHero()
        h.id = hero_obj.id
    
    h.char_id = hero_obj.char_id
    h.oid = hero_obj.original_id
    h.attack = hero_obj.attack
    h.defense = hero_obj.defense
    h.hp = hero_obj.hp
    h.crit = hero_obj.crit
    h.dodge = hero_obj.dodge

    res = h.save()
    if res is not True:
        raise Exception(str(res))
    return h


def delete_cache_hero(_id):
    h = CacheHero.objects.get_by_id(_id)
    if h:
        h.delete()

def get_cache_hero(_id):
    h = CacheHero.objects.get_by_id(_id)
    if h:
        print "CacheHero, hit !!!"
        return h
    
    from core.hero import get_hero_obj
    obj = get_hero_obj(_id)
    
    mongo_char = MongoChar.objects.only('sockets').get(id=obj.char_id)
    sockets = mongo_char.sockets
    for socket in sockets.values():
        if socket['hero'] == _id:
            _add_extra_attr_to_hero(
                obj,
                socket['weapon'],
                socket['armor'],
                socket['jewelry']
            )
            break
    
    h = save_cache_hero(obj)
    return h


def _add_extra_attr_to_hero(hero_obj, weapon, armor, jewelry):
    if weapon:
        this_equip = get_cache_equipment(weapon)
        hero_obj.attack += this_equip.value
    if armor:
        this_equip = get_cache_equipment(armor)
        hero_obj.defense += this_equip.value
    if jewelry:
        this_equip = get_cache_equipment(jewelry)
        hero_obj.hp += this_equip.value
    


def _hero_attribute_change(sender, hero, weapon, armor, jewelry, **kwargs):
    from core.notify import update_hero_notify
    print "_hero_attribute_change", hero, weapon, armor, jewelry
    this_hero = get_cache_hero(hero)
    _add_extra_attr_to_hero(this_hero, weapon, armor, jewelry)
    
    this_hero.save()
    
    char = get_cache_character(this_hero.char_id)
    key = char.notify_key
    update_hero_notify(key, [this_hero])
        

socket_changed_signal.connect(
    _hero_attribute_change,
    dispatch_uid = 'core.cache._hero_attribute_change'
)
