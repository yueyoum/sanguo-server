# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/30/13'


from mongoengine import DoesNotExist
from core.mongoscheme import MongoHero, MongoAchievement, MongoHeroSoul, MongoCharacter
from core.signals import hero_add_signal, hero_del_signal, hero_changed_signal, hero_step_up_signal, hero_to_soul_signal
from core.formation import Formation
from core.exception import SanguoException
from core.resource import check_character
from utils import cache
from utils.functional import id_generator
from core.msgpipe import publish_to_char
from utils import pack_msg
from preset.settings import HERO_MAX_STEP, HERO_START_STEP, HERO_STEP_UP_SOCKET_AMOUNT
from preset.data import HEROS, ACHIEVEMENTS, MONSTERS
from preset import errormsg
import protomsg

from dll import external_calculate

def char_heros_dict(char_id):
    heros = MongoHero.objects.filter(char=char_id)
    return {h.id: h for h in heros}

def char_heros_obj(char_id):
    heros = char_heros_dict(char_id)
    return [Hero.cache_obj(i) for i in heros.keys()]


def cal_hero_property(original_id, level, step):
    """

    @param original_id: hero original id
    @type original_id: int
    @param level: hero level (char level)
    @type level: int
    @return: (attack, defense, hp)
    @rtype: tuple
    """
    hero = HEROS[original_id]

    attack = external_calculate.Hero.attack(level, step, hero.quality, hero.attack_growing)
    defense = external_calculate.Hero.defense(level, step, hero.quality, hero.defense_growing)
    hp = external_calculate.Hero.hp(level, step, hero.quality, hero.hp_growing)

    return attack, defense, hp


def cal_monster_property(oid, level):
    monster = MONSTERS[oid]

    attack = external_calculate.Hero.attack(level, 0, monster.quality, monster.attack)
    defense = external_calculate.Hero.defense(level, 0, monster.quality, monster.defense)
    hp = external_calculate.Hero.hp(level, 0, monster.quality, monster.hp)

    return attack, defense, hp


class FightPowerMixin(object):
    @property
    def power(self):
        a = self.attack * 2.5 * (1 + self.crit / 200.0)
        # b = (self.hp + self.defense * 5) * (1 + self.dodge / 2.0)
        b = self.hp + self.defense * 5
        return int(a + b)


class Hero(FightPowerMixin):
    def __init__(self, hid):
        self.hero = MongoHero.objects.get(id=hid)
        char = MongoCharacter.objects.get(id=self.hero.char)

        self.id = hid
        self.oid = self.hero.oid
        self.step = self.hero.step
        self.progress = self.hero.progress
        self.level = char.level
        self.char_id = char.id

        self.attack, self.defense, self.hp = \
            cal_hero_property(self.oid, self.level, self.step)

        self.model_hero = HEROS[self.oid]
        self.crit = self.model_hero.crit
        self.dodge = self.model_hero.dodge
        self.anger = self.model_hero.anger

        self.default_skill = self.model_hero.default_skill

        self.skills = [int(i) for i in self.model_hero.skills.split(',')]

        self._add_equip_attrs()
        self._add_achievement_buffs()

    def _add_equip_attrs(self):
        from core.item import Equipment
        f = Formation(self.char_id)
        socket = f.find_socket_by_hero(self.id)
        if not socket:
            return

        # 先把装备数值加到人物上
        equipments = []
        for x in ['weapon', 'armor', 'jewelry']:
            equip_id = getattr(socket, x)
            if equip_id:
                equip = Equipment(self.char_id, equip_id)
                self.attack += equip.attack
                self.defense += equip.defense
                self.hp += equip.hp

                equipments.append(equip)

        # 然后加成人物的专属装备
        additions = {}
        special_equipments = self.model_hero.special_equipments
        if special_equipments:
            for equip in equipments:
                _cls = equip.equip.cls
                if _cls not in special_equipments:
                    continue

                _tp = equip.equip.tp
                additions[_tp] = additions.get(_tp, 0) + special_equipments[_cls]

        for _tp, _add_percent in additions.items():
            if _tp == 1:
                # attack
                self.attack *= (1 + _add_percent / 100.0)
            elif _tp == 2:
                # defense
                self.defense *= (1 + _add_percent / 100.0)
            else:
                # hp
                self.hp *= (1 + _add_percent / 100.0)
                self.hp = int(self.hp)

        # 最后再把宝石加上
        for equip in equipments:
            for k, v in equip.gem_attributes.iteritems():
                value = getattr(self, k)
                setattr(self, k, value + v)


    def _add_achievement_buffs(self):
        try:
            mongo_ach = MongoAchievement.objects.get(id=self.char_id)
        except DoesNotExist:
            return

        buffs = {}
        for i in mongo_ach.complete:
            ach = ACHIEVEMENTS[i]
            if not ach.buff_used_for:
                continue

            buffs[ach.buff_used_for] = buffs.get(ach.buff_used_for, 0) + ach.buff_value

        for k, v in buffs.iteritems():
            value = getattr(self, k)
            if k == 'crit':
                new_value = value + v / 100
            else:
                new_value = value * (1 + v / 10000.0)

            new_value = int(new_value)
            setattr(self, k, new_value)


    def save_cache(self):
        cache.set('hero:{0}'.format(self.id), self)

    @staticmethod
    def cache_obj(hid):
        h = cache.get('hero:{0}'.format(hid))
        if h:
            return h

        h = Hero(hid)
        h.save_cache()
        return h


    @property
    def max_socket_amount(self):
        # 当前升阶全部孔数
        if self.step >= HERO_MAX_STEP:
            return 0
        return HERO_STEP_UP_SOCKET_AMOUNT[self.step]

    @property
    def current_socket_amount(self):
        # 当前已经点亮的孔数
        return self.hero.progress


    def _step_up_using_soul(self):
        from core.item import Item
        needs_amount = external_calculate.Hero.step_up_using_soul_amount(self.model_hero.quality)

        hs = HeroSoul(self.char_id)
        self_soul_amount = hs.soul_amount(self.oid)

        amount_diff = needs_amount - self_soul_amount
        if amount_diff >= 0:
            item = Item(self.char_id)
            if not item.has_stuff(22, amount_diff):
                raise SanguoException(
                    errormsg.HERO_STEP_UP_ALL_NOT_ENOUGH,
                    self.char_id,
                    "Hero Step Up",
                    "soul not enough"
                )
            item.stuff_remove(22, amount_diff)

        hs.purge_soul(self.oid)

    def step_up(self):
        # 升阶
        if self.step >= HERO_MAX_STEP:
            raise SanguoException(
                errormsg.HERO_REACH_MAX_STEP,
                self.char_id,
                "Hero Step Up",
                "Hero {0} reach max step {1}".format(self.id, HERO_MAX_STEP)
            )

        cost_gold = external_calculate.Hero.step_up_using_gold(self.model_hero.quality)

        with check_character(self.char_id, gold=-cost_gold, func_name="Hero Step Up"):
            self._step_up_using_soul()


        # 扣完东西了，开始搞一次
        self.hero.progress += 1
        if self.hero.progress >= self.max_socket_amount:
            # 真正的升阶
            # 否则仅仅是记录当前状态
            self.hero.step += 1
            self.hero.progress = 0

            hero_step_up_signal.send(
                sender=None,
                char_id=self.char_id,
                hero_id=self.id,
                new_step=self.hero.step
            )

        self.hero.save()
        hero_changed_signal.send(
            sender=None,
            hero_id=self.id
        )


class HeroSoul(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mongo_hs = MongoHeroSoul.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mongo_hs = MongoHeroSoul(id=self.char_id)
            self.mongo_hs.souls = {}
            self.mongo_hs.save()

    def soul_amount(self, _id):
        return self.mongo_hs.souls.get(str(_id), 0)

    def has_soul(self, _id, amount=1):
        return self.soul_amount(_id) >= amount

    def add_soul(self, souls):
        new_souls = []
        update_souls = []
        for _id, amount in souls:
            str_id = str(_id)
            if str_id in self.mongo_hs.souls:
                self.mongo_hs.souls[str_id] += amount
                update_souls.append((_id, self.mongo_hs.souls[str_id]))
            else:
                self.mongo_hs.souls[str_id] = amount
                new_souls.append((_id, amount))

        self.mongo_hs.save()
        if new_souls:
            msg = protomsg.AddHeroSoulNotify()
            for _id, amount in new_souls:
                s = msg.herosouls.add()
                s.id = _id
                s.amount = amount

            publish_to_char(self.char_id, pack_msg(msg))

        if update_souls:
            msg = protomsg.UpdateHeroSoulNotify()
            for _id, amount in update_souls:
                s = msg.herosouls.add()
                s.id = _id
                s.amount = amount

            publish_to_char(self.char_id, pack_msg(msg))


    def remove_soul(self, souls):
        remove_souls = []
        update_souls = []
        for _id, amount in souls:
            if not self.has_soul(_id, amount):
                raise SanguoException(
                    errormsg.SOUL_NOT_ENOUGH,
                    self.char_id,
                    "HeroSoul Remove",
                    "HeroSoul {0} not enough/exist, expected amount {1}".format(_id, amount)
                )

        for _id, amount in souls:
            str_id = str(_id)
            self.mongo_hs.souls[str_id] -= amount
            if self.mongo_hs.souls[str_id] <= 0:
                remove_souls.append(_id)
                self.mongo_hs.souls.pop(str_id)
            else:
                update_souls.append((_id, self.mongo_hs.souls[str_id]))

        self.mongo_hs.save()
        if remove_souls:
            msg = protomsg.RemoveHeroSoulNotify()
            msg.ids.extend(remove_souls)

            publish_to_char(self.char_id, pack_msg(msg))

        if update_souls:
            msg = protomsg.UpdateHeroSoulNotify()
            for _id, amount in update_souls:
                s = msg.herosouls.add()
                s.id = _id
                s.amount = amount

            publish_to_char(self.char_id, pack_msg(msg))


    def purge_soul(self, _id):
        self.mongo_hs.souls.pop(str(_id))
        self.mongo_hs.save()

        msg = protomsg.RemoveHeroSoulNotify()
        msg.ids.append(_id)
        publish_to_char(self.char_id, pack_msg(msg))


    def send_notify(self):
        msg = protomsg.HeroSoulNotify()
        for _id, amount in self.mongo_hs.souls.iteritems():
            s = msg.herosouls.add()
            s.id = int(_id)
            s.amount = amount

        publish_to_char(self.char_id, pack_msg(msg))

class SaveHeroResult(object):
    __slots__ = ['id_range', 'actual_heros', 'to_souls']


def save_hero(char_id, hero_original_ids, add_notify=True):
    if not isinstance(hero_original_ids, (list, tuple)):
        hero_original_ids = [hero_original_ids]

    char_heros = MongoHero.objects.filter(char=char_id)
    char_hero_oids = set( [h.oid for h in char_heros] )

    to_soul_hero_ids = []
    for h in hero_original_ids[:]:
        if h in char_hero_oids:
            to_soul_hero_ids.append(h)
            hero_original_ids.remove(h)

    souls = {}
    if to_soul_hero_ids:
        for sid in to_soul_hero_ids:
            this_hero = HEROS[sid]
            souls[this_hero.id] = souls.get(this_hero.id, 0) + 1

        for k in souls.keys():
            souls[k] *= external_calculate.Hero.step_up_using_soul_amount(HEROS[k].quality)

        hs = HeroSoul(char_id)
        hs.add_soul(souls.items())

        hero_to_soul_signal.send(
            sender=None,
            char_id=char_id,
            souls=souls.items(),
        )

    id_range = []
    if hero_original_ids:
        length = len(hero_original_ids)
        id_range = id_generator('charhero', length)
        for i, _id in enumerate(id_range):
            MongoHero(id=_id, char=char_id, oid=hero_original_ids[i], step=HERO_START_STEP, progress=0).save()

        hero_add_signal.send(
            sender=None,
            char_id=char_id,
            hero_ids=id_range,
            hero_original_ids=hero_original_ids,
            send_notify=add_notify,
        )

    res = SaveHeroResult()
    res.id_range = id_range
    res.actual_heros = hero_original_ids
    res.to_souls = souls.items()
    return res


def delete_hero(char_id, ids):
    # XXX
    # 只能删除背包中的英雄，不能删除在阵法中的。注意！
    """

    @param char_id: char id
    @type char_id: int
    @param ids: hero ids
    @type ids: list | tuple
    """
    for i in ids:
        MongoHero.objects(id=i).delete()

    hero_del_signal.send(
        sender=None,
        char_id=char_id,
        hero_ids=ids
    )
