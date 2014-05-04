# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/29/14'

from contextlib import contextmanager

from core.exception import SanguoException

from preset.errormsg import GOLD_NOT_ENOUGH, SYCEE_NOT_ENOUGH, STUFF_NOT_ENOUGH, GEM_NOT_ENOUGH

@contextmanager
def check_character(char_id, gold=0, sycee=0, save=True, func_name=""):
    from core.character import Char
    c = Char(char_id)
    mc = c.mc
    if gold < 0 and mc.gold < abs(gold):
        raise SanguoException(GOLD_NOT_ENOUGH, char_id, func_name, 'Gold Not Enough. {0} < {1}'.format(mc.gold, abs(gold)))
    if sycee < 0 and mc.sycee < abs(sycee):
        raise SanguoException(SYCEE_NOT_ENOUGH, char_id, func_name, 'Sycee Not Enough. {0} < {1}'.format(mc.sycee, abs(sycee)))

    yield None

    if gold !=0 or sycee != 0:
        if save:
            c.update(gold=gold, sycee=sycee, des='{0}, gold: {1}, sycee: {2}'.format(func_name, gold, sycee))


@contextmanager
def check_stuff(char_id, stuffs, func_name=""):
    # stuffs = [(id, amount), (id, amount)...]
    from core.item import Item
    item = Item(char_id)
    for _id, _amount in stuffs:
        if not item.has_stuff(_id, _amount):
            raise SanguoException(STUFF_NOT_ENOUGH, char_id, func_name, 'Stuff {0} Not Enough. Excepted Amount {1}'.format(_id, _amount))

    yield None

    for _id, _amount in stuffs:
        item.stuff_remove(_id, _amount)


@contextmanager
def check_gem(char_id, gems, func_name=""):
    # gems = [(id, amount), (id, amount)...]
    from core.item import Item
    item = Item(char_id)
    for _id, _amount in gems:
        if not item.has_gem(_id, _amount):
            raise SanguoException(GEM_NOT_ENOUGH, char_id, func_name, 'Gem {0} Not Enough. Excepted Amount {1}'.format(_id, _amount))

    yield None
    for _id, _amount in gems:
        item.gem_remove(_id, _amount)
