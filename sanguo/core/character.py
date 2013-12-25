# -*- coding: utf-8 -*-
from mongoengine import DoesNotExist

from apps.character.models import Character
from apps.character.cache import get_cache_character
from apps.item.cache import get_cache_equipment
from core import GLOBAL
from core.cache import get_cache_hero
from core.counter import Counter
from core.formation import save_formation, save_socket, get_char_formation
from core.hero import save_hero, delete_hero
from core.mongoscheme import Hang, MongoChar, MongoHero, MongoPrison
from preset.settings import COUNTER, CHAR_INITIALIZE
from core.signals import char_changed_signal



COUNTER_KEYS = COUNTER.keys()


def update_needs_exp(level):
    exp = pow(level, 2.5) + level * 20
    return int(round(exp * 10, -1))
    


class Char(object):
    def __init__(self, char_id=None, **kwargs):
        if not char_id:
            account_id = kwargs['account_id']
            server_id = kwargs['server_id']
            name = kwargs['name']
            char = char_initialize(account_id, server_id, name)
            self.id = char.id
        else:
            self.id = char_id
    
    
    def delete(self):
        # WARNING
        # 一般不删除角色
        Character.objects.filter(id=char_id).delete()
        MongoChar.objects.get(id=char_id).delete()
        MongoHero.objects.filter(char=char_id).delete()
        try:
            MongoPrison.objects.get(id=char_id).delete()
            Hang.objects.get(id=char_id).delete()
        except DoesNotExist:
            pass
    
    @property
    def cacheobj(self):
        return get_cache_character(self.id)
    
    
    # 阵法
    @property
    def formation(self):
        return get_char_formation(self.id)
    
    @property
    def sockets(self):
        c = MongoChar.objects.only('sockets').get(id=self.id)
        return {int(k): v for k, v in c.sockets.iteritems()}
    
    def save_formation(self, socket_ids, send_notify=True):
        save_formation(self.id, socket_ids, send_notify=send_notify)
    
    def save_socket(self, socket_id=None, hero=0, weapon=0, armor=0, jewelry=0):
        save_socket(
            self.id,
            socket_id = socket_id,
            hero = hero,
            weapon = weapon,
            armor = armor,
            jewelry = jewelry
        )
    
    
    
    # 武将
    @property
    def heros_dict(self):
        heros = MongoHero.objects.filter(char=self.id)
        return {h.id: h.oid for h in heros}
        
    @property
    def heros(self):
        return [get_cache_hero(i) for i in self.heros_dict.keys()]
    
    def save_hero(self, hero_original_ids, add_notify=True):
        return save_hero(self.id, hero_original_ids, add_notify=add_notify)
    
    def delete_hero(self, ids):
        delete_hero(self.id, ids)
    
    def in_bag_hero_ids(self):
        heros = MongoHero.objects.filter(char=self.id)
        hero_ids = [h.id for h in heros]
        mongo_char = MongoChar.objects.only('sockets').get(id=self.id)
        for s in mongo_char.sockets.values():
            if s.hero:
                hero_ids.remove(s.hero)
        return hero_ids
    
    
    @property
    def power(self):
        heros = self.heros
        p = 0
        for h in heros:
            p += h.power
        return p
    
        
    
    # 装备
    @property
    def equip_ids(self):
        char = MongoChar.objects.only('equips').get(id=self.id)
        return char.equips
    
    @property
    def equipments(self):
        char = MongoChar.objects.only('equips').get(id=self.id)
        equip_ids = char.equips
        objs = [get_cache_equipment(eid) for eid in equip_ids]
        return objs
    
    def update(self, gold=0, sycee=0, exp=0, honor=0, renown=0):
        char = Character.objects.get(id=self.id)
        char.gold += gold
        char.sycee += sycee
        
        if exp:
            new_exp = char.exp + exp
            level = char.level
            while True:
                need_exp = update_needs_exp(level)
                if new_exp < update_needs_exp:
                    break
                
                level += 1
                new_exp -= update_needs_exp
            
            char.exp = new_exp
            char.level = level
            
        print 'char.update,', char.exp, char.level
        # TODO honor
        char.save()
        
        char_changed_signal.send(
            sender = None,
            char_id = self.id
        )
    
    
    @property
    def gems(self):
        char = MongoChar.objects.only('gems').get(id=self.id)
        return {int(k): v for k, v in char.gems.iteritems()}
    
    
    
    def _incr_exp(self, exp):
        pass



def char_initialize(account_id, server_id, name):
    from core.prison import Prison

    init_gold = CHAR_INITIALIZE.get('gold', 0)
    init_sycee = CHAR_INITIALIZE.get('sycee', 0)
    init_level = CHAR_INITIALIZE.get('level', 1)
    init_official = CHAR_INITIALIZE.get('official', 1)
    
    char = Character.objects.create(
        account_id = account_id,
        server_id = server_id,
        name = name,
        gold = init_gold,
        sycee = init_sycee,
        level = init_level,
        official = init_official,
    )
    char_id = char.id
    
    MongoChar(id=char_id).save()
    Prison(char_id)
    
    for func_name in COUNTER_KEYS:
        Counter(char_id, func_name)
    
    init_hero_ids = CHAR_INITIALIZE.get('heros', [])
    if not init_hero_ids:
        init_hero_ids = GLOBAL.HEROS.get_random_hero_ids(3)
    
    init_equips = CHAR_INITIALIZE.get('equips', [])
    if init_equips:
        from core.equip import generate_and_save_equip
        for tid, level in init_equips:
            generate_and_save_equip(tid, level ,char_id)
    
    init_gems = CHAR_INITIALIZE.get('gems', [])
    if init_gems:
        from core.gem import save_gem
        save_gem(init_gems, char_id)
    
    hero_ids = save_hero(char_id, init_hero_ids, add_notify=False)
    for index, _id in enumerate(hero_ids):
        save_socket(char_id, socket_id=index+1, hero=_id, send_notify=False)

    socket_ids = [
            1, 0, 0,
            2, 0, 0,
            3, 0, 0,
            ]

    save_formation(char_id, socket_ids, send_notify=False)

    # 将关卡1设置为new 可进入
    MongoChar.objects(id=char_id).update_one(set__stage_new=1)
    
    return char


def delete_char(char_id):
    # WARNING
    # 一般不删除角色
    Character.objects.filter(id=char_id).delete()
    MongoChar.objects.get(id=char_id).delete()
    MongoHero.objects.filter(char=char_id).delete()
    try:
        MongoPrison.objects.get(id=char_id).delete()
        Hang.objects.get(id=char_id).delete()
    except DoesNotExist:
        pass

