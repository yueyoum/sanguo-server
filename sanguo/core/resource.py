# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/29/14'

import logging
from contextlib import contextmanager

import arrow
from django.conf import settings

from core.exception import SanguoException

from preset.errormsg import GOLD_NOT_ENOUGH, SYCEE_NOT_ENOUGH, STUFF_NOT_ENOUGH, GEM_NOT_ENOUGH, SOUL_NOT_ENOUGH, EQUIPMENT_NOT_EXIST

logger = logging.getLogger('sanguo')

TIME_ZONE = settings.TIME_ZONE

# 对于要消耗的资源进行检查，
# 目前系统不支持消耗卡牌，经验，官职经验，所以不支持消耗这些资源

def _check_character(char_id, gold=0, sycee=0, func_name=""):
    from core.character import Char
    c = Char(char_id)
    mc = c.mc
    if gold < 0 and mc.gold < abs(gold):
        raise SanguoException(GOLD_NOT_ENOUGH, char_id, func_name, 'Gold Not Enough. {0} < {1}'.format(mc.gold, abs(gold)))
    if sycee < 0 and mc.sycee < abs(sycee):
        raise SanguoException(SYCEE_NOT_ENOUGH, char_id, func_name, 'Sycee Not Enough. {0} < {1}'.format(mc.sycee, abs(sycee)))

    yield

    if gold or sycee:
        c.update(gold=gold, sycee=sycee)


def _check_hero_soul(char_id, souls, func_name=""):
    from core.hero import HeroSoul
    hs = HeroSoul(char_id)
    for _id, _amount in souls:
        if not hs.has_soul(_id, _amount):
            raise SanguoException(SOUL_NOT_ENOUGH, char_id, func_name, 'Soul {0} Not Enough/Exist.'.format(_id))

    yield

    hs.remove_soul(souls)

def _check_equipment(char_id, ids, func_name=""):
    from core.item import Item
    item = Item(char_id)
    for _id in ids:
        if not item.has_equip(_id):
            raise SanguoException(EQUIPMENT_NOT_EXIST, char_id, func_name, 'Equipment {0} Not Exist'.format(_id))

    yield

    item.equip_remove(ids)


def _check_gems(char_id, gems, func_name=""):
    from core.item import Item
    item = Item(char_id)
    for _id, _amount in gems:
        if not item.has_gem(_id, _amount):
            raise SanguoException(GEM_NOT_ENOUGH, char_id, func_name, 'Gem {0} Not Enough/Exist'.format(_id))

    yield

    for _id, _amount in gems:
        item.gem_remove(_id, _amount)


def _check_stuffs(char_id, stuffs, func_name=""):
    from core.item import Item
    item = Item(char_id)
    for _id, _amount in stuffs:
        if not item.has_stuff(_id, _amount):
            raise SanguoException(STUFF_NOT_ENOUGH, char_id, func_name, 'Stuff {0} Not Enough/Exist'.format(_id))

    yield

    for _id, _amount in stuffs:
        item.stuff_remove(_id, _amount)


def _get_resource_data(**kwargs):
    data = {
        'exp': kwargs.get('exp', 0),
        'official_exp': kwargs.get('official_exp', 0),
        'gold': kwargs.get('gold', 0),
        'sycee': kwargs.get('sycee', 0),
        'heros': kwargs.get('heros', []),
        'souls': kwargs.get('souls', []),
        'equipments': kwargs.get('equipments', []),
        'gems': kwargs.get('gems', []),
        'stuffs': kwargs.get('stuffs', []),
    }
    return data


class Resource(object):
    __slots__ = ['char_id', 'func_name', 'des']
    def __init__(self, char_id, func_name, des=''):
        self.char_id = char_id
        self.func_name = func_name
        self.des = des


    def _pre_check(self, data):
        callbacks = []
        if data['gold'] or data['sycee']:
            callbacks.append(_check_character(self.char_id, gold=data['gold'], sycee=data['sycee'], func_name=self.func_name))

        if data['souls']:
            callbacks.append(_check_hero_soul(self.char_id, data['souls'], func_name=self.func_name))

        if data['equipments']:
            callbacks.append(_check_equipment(self.char_id, data['equipments'], func_name=self.func_name))

        if data['gems']:
            callbacks.append(_check_gems(self.char_id, data['gems'], func_name=self.func_name))

        if data['stuffs']:
            callbacks.append(_check_stuffs(self.char_id, data['stuffs'], func_name=self.func_name))

        for cb in callbacks:
            cb.next()

        return callbacks

    def _post_check(self, callbacks):
        for cb in callbacks:
            try:
                cb.next()
            except StopIteration:
                pass


    @contextmanager
    def check(self, **kwargs):
        data = _get_resource_data(**kwargs)
        callbacks = self._pre_check(data)

        yield

        self._post_check(callbacks)

        data['income'] = 0
        data['func_name'] = self.func_name
        data['des'] = self.des
        resource_logger(self.char_id, data)


    def check_and_remove(self, **kwargs):
        data = _get_resource_data(**kwargs)
        callbacks = self._pre_check(data)
        self._post_check(callbacks)

        data['income'] = 0
        data['func_name'] = self.func_name
        data['des'] = self.des
        resource_logger(self.char_id, data)


    def add(self, **kwargs):
        from core.character import Char
        from core.hero import save_hero, HeroSoul
        from core.item import Item

        data = _get_resource_data(**kwargs)
        purchase_got = kwargs.get('purchase_got', 0)
        purchase_actual_got = kwargs.get('purchase_actual_got', 0)

        if data['gold'] or data['sycee'] or data['exp'] or data['official_exp'] or purchase_got:
            char = Char(self.char_id)
            char.update(gold=data['gold'], sycee=data['sycee'], exp=data['exp'], official_exp=data['official_exp'],
                        purchase_got=purchase_got,
                        purchase_actual_got=purchase_actual_got,
                        )
    
        if data['heros']:
            heros = []
            for _id, _amount in data['heros']:
                heros.extend([_id] * _amount)
            sh_res = save_hero(self.char_id, heros)
    
        if data['souls']:
            hs = HeroSoul(self.char_id)
            hs.add_soul(data['souls'])
    
        item = Item(self.char_id)
        for _id, _level, _amount in data['equipments']:
            for i in range(_amount):
                item.equip_add(_id, _level)
    
        if data['gems']:
            item.gem_add(data['gems'])
    
        if data['stuffs']:
            item.stuff_add(data['stuffs'])
    
        # normalize the data
        if data['heros']:
            data['heros'] = sh_res.actual_heros
            souls = dict(data['souls'])
    
            for _sid, _samount in sh_res.to_souls:
                souls[_sid] = souls.get(_sid, 0) + _samount

            data['souls'] = souls.items()

        data['income'] = 1
        data['func_name'] = self.func_name
        data['des'] = self.des
        resource_logger(self.char_id, data)

        data.pop('income')
        data.pop('func_name')
        data.pop('des')
        return data


def resource_logger(char_id, data):
    extra = {
        'log_type_id': 2,
        'char_id': char_id,
        'occurred_at': arrow.utcnow().to(TIME_ZONE).format('YYYY-MM-DD HH:mm:ss'),
    }

    extra.update(data)
    logger.info("Resource Change. Char Id {0}. Extra: {1}".format(char_id, extra), extra=extra)
