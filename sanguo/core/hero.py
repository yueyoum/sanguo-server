# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/30/13'


from mongoengine import DoesNotExist
from core.mongoscheme import MongoHero, MongoAchievement, MongoHeroSoul, MongoCharacter, MongoEmbeddedHeroWuxing
from core.signals import hero_add_signal, hero_changed_signal, hero_step_up_signal, hero_to_soul_signal, hero_del_signal
from core.formation import Formation
from core.exception import SanguoException
from core.resource import Resource
from core.horse import Horse
from core.msgpipe import publish_to_char
from core.common import FightPowerMixin, level_up
from core.times_log import TimesLogHeroStepUp
from core.activity import ActivityEntry, ActivityStatic

from utils import cache
from utils import pack_msg
from utils.functional import id_generator

from preset.settings import HERO_MAX_STEP, HERO_START_STEP, HERO_STEP_UP_SOCKET_AMOUNT
from preset.data import HEROS, ACHIEVEMENTS, MONSTERS, HORSE, WUXING, WUXING_LEVEL, WUXING_MAX_LEVEL
from preset import errormsg
import protomsg

from dll import external_calculate

def char_heros_dict(char_id):
    heros = MongoHero.objects.filter(char=char_id)
    return {h.id: h for h in heros}

def char_heros_obj(char_id):
    heros = char_heros_dict(char_id)
    result = []
    for hid in heros.keys():
        h = Hero(hid)
        h.save_cache()
        result.append(h)

    return result

def char_heros_amount(char_id, filter_quality=None):
    heros = char_heros_dict(char_id).values()
    if filter_quality == None:
        return len(heros)

    filtered = [h for h in heros if HEROS[h.oid].quality == filter_quality]
    return len(filtered)

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


class HeroWuXing(object):
    __slots__ = ['id', 'level', 'exp', 'obj']
    def __init__(self, _id, level, exp):
        self.id = _id
        self.level = level
        self.exp = exp
        self.obj = WUXING[_id]


    @staticmethod
    def update_need_exp(level):
        try:
            return WUXING_LEVEL[level].exp
        except KeyError:
            return 0

    @property
    def max_exp(self):
        return HeroWuXing.update_need_exp(self.level)


    def update(self, add_exp):
        self.level, self.exp = level_up(self.level, self.exp, add_exp, HeroWuXing.update_need_exp)


    def to_proto(self):
        msg = protomsg.Hero.WuXing()
        msg.id = self.id
        msg.level = self.level
        msg.cur_exp = self.exp
        return msg


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
        self._add_global_buffs()


    def save_cache(self):
        cache.set('hero:{0}'.format(self.id), self, expire=3600*3)


    @staticmethod
    def cache_obj(hid):
        h = cache.get('hero:{0}'.format(hid))
        if h:
            return h

        h = Hero(hid)
        h.save_cache()
        return h


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

        # 马
        if socket.horse:
            horse = Horse(self.char_id).mongo_horse.horses[str(socket.horse)]
            self.attack += horse.attack
            self.defense += horse.defense
            self.hp += horse.hp
            self.crit += int(HORSE[horse.oid].crit / 10)


    def _add_global_buffs(self):
        from core.union.store import UnionStore
        s = UnionStore(self.char_id)
        buffs = s.get_add_buffs_with_string_name()
        for k, v in buffs.iteritems():
            value = getattr(self, k)
            new_value = int(value + v)
            setattr(self, k, new_value)

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


    def get_step_up_gold_needs(self):
        if self.model_hero.quality == 1:
            return 10000
        if self.model_hero.quality == 2:
            return 5000
        if self.model_hero.quality == 3:
            return 1000

        raise RuntimeError("Invalid Hero Quality: {0}".format(self.model_hero.quality))

    def get_step_up_soul_needs(self):
        if self.model_hero.quality == 1:
            return 100
        if self.model_hero.quality == 2:
            return 75
        if self.model_hero.quality == 3:
            return 40

        raise RuntimeError("Invalid Hero Quality: {0}".format(self.model_hero.quality))


    def step_up(self):
        # 升阶
        if self.step >= HERO_MAX_STEP:
            raise SanguoException(
                errormsg.HERO_REACH_MAX_STEP,
                self.char_id,
                "Hero Step Up",
                "Hero {0} reach max step {1}".format(self.id, HERO_MAX_STEP)
            )

        resource_needs = {}
        cost_gold = self.get_step_up_gold_needs()

        resource_needs['gold'] = -cost_gold
        soul_needs_amount = self.get_step_up_soul_needs()

        resource_needs['souls'] = [(self.oid, soul_needs_amount)]

        hs = HeroSoul(self.char_id)
        self_soul_amount = hs.soul_amount(self.oid)
        common_soul_needs = soul_needs_amount - self_soul_amount
        if common_soul_needs > 0:
            # need common soul
            resource_needs['stuffs'] = [(22, common_soul_needs)]

        resource = Resource(self.char_id, "Hero Step Up", 'step up {0}'.format(self.id))
        try:
            resource.check_and_remove(**resource_needs)
        except SanguoException as e:
            if e.error_id == errormsg.SOUL_NOT_ENOUGH or e.error_id == errormsg.STUFF_NOT_ENOUGH:
                raise SanguoException(
                    errormsg.HERO_STEP_UP_ALL_NOT_ENOUGH,
                    self.char_id,
                    "Hero Step Up",
                    "soul not enough"
                )
            raise e

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

        self.step = self.hero.step
        self.hero.save()
        hero_changed_signal.send(
            sender=None,
            hero_id=self.id
        )

        TimesLogHeroStepUp(self.char_id).inc()
        if self.step >= 5:
            ae  =ActivityEntry(self.char_id, 40004)
            if ae:
                ae.enable(self.step)
                ActivityStatic(self.char_id).send_update_notify(activity_ids=[40004])


    def wuxing_update(self, wuxing_id, souls):
        # 五行升级
        str_id = str(wuxing_id)
        if str_id not in self.hero.wuxings:
            raise SanguoException(
                errormsg.WUXING_NOT_FOR_THIS_HERO,
                self.char_id,
                "Hero WuXing Update",
                "hero {0} has no wuxing {1}".format(self.id, wuxing_id)
            )

        hs = HeroSoul(self.char_id)
        add_exp = 0
        for soul_id, soul_amount in souls:
            if not hs.has_soul(soul_id, soul_amount):
                raise SanguoException(
                    errormsg.SOUL_NOT_ENOUGH,
                    self.char_id,
                    "Hero WuXing Update",
                    "soul not enough. {0}: {1}".format(soul_id, soul_amount)
                )

            add_exp += HEROS[soul_id].wuxing_exp * soul_amount

        wx = HeroWuXing(wuxing_id, self.hero.wuxings[str_id].level, self.hero.wuxings[str_id].exp)
        wx.update(add_exp)

        hs.remove_soul(souls)

        self.hero.wuxings[str_id].level = wx.level
        self.hero.wuxings[str_id].exp = wx.exp
        self.hero.save()
        hero_changed_signal.send(
            sender=None,
            hero_id=self.id
        )

        if wx.level >= 5:
            ae = ActivityEntry(self.char_id, 40003)
            if ae:
                ae.enable(wx.level)

                ActivityStatic(self.char_id).send_update_notify(activity_ids=[40003])


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

        for _id, _ in souls:
            if _id not in HEROS:
                raise RuntimeError("soul {0} not exist".format(_id))

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

class _SaveHeroResult(object):
    __slots__ = ['id_range', 'actual_heros', 'to_souls']

class _FakeSaveHeroResult(object):
    __slots__ = ['id_range', 'actual_heros', 'to_souls']
    def __init__(self):
        self.id_range = []
        self.actual_heros = []
        self.to_souls = []

    def __bool__(self):
        return False
    __nonzero__ = __bool__


FakeSaveHeroResult = _FakeSaveHeroResult()


def get_char_hero_oids(char_id):
    docs = MongoHero._get_collection().find(
            {'char': char_id},
            {'oid': 1}
    )
    return [doc['oid'] for doc in docs]


SAVE_HERO_TO_SOUL_TABLE = {
    1: 40,
    2: 20,
    3: 10
}


def save_hero(char_id, hero_original_ids, add_notify=True):
    if not isinstance(hero_original_ids, (list, tuple)):
        hero_original_ids = [hero_original_ids]

    char_hero_oids = get_char_hero_oids(char_id)

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
            souls[k] *= SAVE_HERO_TO_SOUL_TABLE[ HEROS[k].quality ]

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
            mh = MongoHero(id=_id)
            mh.char = char_id
            mh.oid = hero_original_ids[i]
            mh.step = HERO_START_STEP
            mh.progress = 0

            wuxing = {
                str( HEROS[mh.oid].wuxings[0] ): MongoEmbeddedHeroWuxing(level=1, exp=0)
            }

            mh.wuxings = wuxing
            mh.save()

        hero_add_signal.send(
            sender=None,
            char_id=char_id,
            hero_ids=id_range,
            hero_original_ids=hero_original_ids,
            send_notify=add_notify,
        )

    res = _SaveHeroResult()
    res.id_range = id_range
    res.actual_heros = [(oid, 1) for oid in hero_original_ids]
    res.to_souls = souls.items()
    return res


def recruit_hero(char_id, _id):
    if _id not in HEROS:
        raise SanguoException(
            errormsg.SOUL_CAN_NOT_RECRUIT,
            char_id,
            "Recruit Hero",
            "Soul {0} not exist".format(_id)
        )

    char_hero_oids = get_char_hero_oids(char_id)
    if _id in char_hero_oids:
        raise SanguoException(
            errormsg.SOUL_CAN_NOT_RECRUIT,
            char_id,
            "Recruit Hero",
            "Hero {0} already exist".format(_id)
        )


    soul_amount = external_calculate.Hero.step_up_using_soul_amount(HEROS[_id].quality)
    hs = HeroSoul(char_id)
    hs.remove_soul([(_id, soul_amount)])

    save_hero(char_id, [_id])


def break_hero(char_id, _id):
    # 主动将武将转为卡魂
    try:
        h = char_heros_dict(char_id)[_id]
    except KeyError:
        raise SanguoException(
            errormsg.HERO_NOT_EXSIT,
            char_id,
            "Hero Break",
            "hero {0} not exist".format(_id)
        )

    formation = Formation(char_id)
    if _id in formation.in_formation_hero_ids():
        raise SanguoException(
            errormsg.HERO_CANNOT_BREAK_IN_FORMATION,
            char_id,
            "Hero Break",
            "hero {0} in formation, cannot break".format(_id)
        )

    oid = h.oid
    quality = HEROS[oid].quality
    souls_amount = SAVE_HERO_TO_SOUL_TABLE[quality]

    MongoHero.objects.get(id=_id).delete()

    hero_del_signal.send(
        sender=None,
        char_id=char_id,
        hero_id=_id,
        hero_oid=oid
    )

    HeroSoul(char_id).add_soul([(oid, souls_amount)])

