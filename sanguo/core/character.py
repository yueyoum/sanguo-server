# -*- coding: utf-8 -*-
from mongoengine import DoesNotExist

from apps.character.models import Character
from core.counter import Counter
from core.hero import save_hero, delete_hero, Hero
from core.mongoscheme import Hang, MongoHero, MongoPrison
from preset.settings import COUNTER, CHAR_INITIALIZE
from core.signals import char_changed_signal, char_updated_signal

from core.formation import Formation

COUNTER_KEYS = COUNTER.keys()


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
        Character.objects.filter(id=self.id).delete()
        # MongoChar.objects.get(id=self.id).delete()
        # FIXME mongoscheme 中的全要删除
        MongoHero.objects.filter(char=self.id).delete()
        try:
            MongoPrison.objects.get(id=self.id).delete()
            Hang.objects.get(id=self.id).delete()
        except DoesNotExist:
            pass

    @property
    def cacheobj(self):
        return Character.cache_obj(self.id)

    # 阵法
    @property
    def formation(self):
        f = Formation(self.id)
        return f.formation.formation

    @property
    def sockets(self):
        f = Formation(self.id)
        c = f.formation.sockets
        return {int(k): v for k, v in c.iteritems()}

    @property
    def hero_oid_list(self):
        # 阵法中英雄按照排列顺序的原始ID列表
        heros_dict = self.heros_dict
        f = Formation(self.id)
        c = f.formation
        res = []
        for f in c.formation:
            if f == 0:
                res.append(0)
                continue

            s = c.sockets[str(f)]
            if not s.hero:
                continue

            res.append(heros_dict[s.hero])
        return res



    # 武将
    @property
    def heros_dict(self):
        heros = MongoHero.objects.filter(char=self.id)
        return {h.id: h.oid for h in heros}

    @property
    def heros(self):
        return [Hero.cache_obj(i) for i in self.heros_dict.keys()]

    def save_hero(self, hero_original_ids, add_notify=True):
        return save_hero(self.id, hero_original_ids, add_notify=add_notify)

    def delete_hero(self, ids):
        delete_hero(self.id, ids)

    def in_bag_hero_ids(self):
        heros = MongoHero.objects.filter(char=self.id)
        hero_ids = [h.id for h in heros]
        f = Formation(self.id)
        for s in f.formation.sockets.values():
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


    def update(self, gold=0, sycee=0, exp=0, honor=0, renown=0):
        char = Character.objects.get(id=self.id)
        char.gold += gold
        char.sycee += sycee
        char.renown += renown

        if exp:
            new_exp = char.exp + exp
            level = char.level
            old_level = char.level
            while True:
                need_exp = char.update_needs_exp(level)
                if new_exp < need_exp:
                    break

                level += 1
                new_exp -= need_exp

            char.exp = new_exp
            char.level = level

            if char.level != old_level:
                char_updated_signal.send(
                    sender=None,
                    char_id=self.id
                )

        # TODO honor
        char.save()

        char_changed_signal.send(
            sender=None,
            char_id=self.id
        )



def char_initialize(account_id, server_id, name):
    from core.prison import Prison

    init_gold = CHAR_INITIALIZE.get('gold', 0)
    init_sycee = CHAR_INITIALIZE.get('sycee', 0)
    init_level = CHAR_INITIALIZE.get('level', 1)
    init_official = CHAR_INITIALIZE.get('official', 1)

    char = Character.objects.create(
        account_id=account_id,
        server_id=server_id,
        name=name,
        gold=init_gold,
        sycee=init_sycee,
        level=init_level,
        official=init_official,
    )
    char_id = char.id

    Prison(char_id)

    for func_name in COUNTER_KEYS:
        Counter(char_id, func_name)

    init_hero_ids = CHAR_INITIALIZE.get('heros', [])



    hero_ids = save_hero(char_id, init_hero_ids, add_notify=False)
    socket_ids = []
    f = Formation(char_id)

    for index, _id in enumerate(hero_ids):
        h = Hero.cache_obj(_id)
        _sid = f.save_socket(hero=_id,
                           send_notify=False)
        socket_ids.append(_sid)

    socket_ids = [
        socket_ids[0], 0, 0,
        socket_ids[1], 0, 0,
        socket_ids[2], 0, 0,
    ]

    f.save_formation(socket_ids, send_notify=False)
    # 将关卡1设置为new 可进入

    return char
