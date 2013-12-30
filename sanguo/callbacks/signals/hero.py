from core.hero.cache import get_cache_hero, add_extra_attr_to_hero
from core.signals import (
    hero_add_signal,
    hero_del_signal,
    hero_changed_signal,
    socket_changed_signal,
    )

from core.notify import (
    add_hero_notify,
    remove_hero_notify,
    update_hero_notify,
    )

from utils import cache


def _hero_add(char_id, hero_ids, **kwargs):
    heros = [get_cache_hero(i) for i in hero_ids]
    add_hero_notify(char_id, heros)


def _hero_del(char_id, hero_ids, **kwargs):
    remove_hero_notify(char_id, hero_ids)


def _hero_change(cache_hero_obj, **kwargs):
    update_hero_notify(
        cache_hero_obj.char_id,
        [cache_hero_obj]
    )


hero_add_signal.connect(
    _hero_add,
    dispatch_uid='core.callbacks.hero._hero_add'
)

hero_del_signal.connect(
    _hero_del,
    dispatch_uid='core.callbacks.hero._hero_del'
)

hero_changed_signal.connect(
    _hero_change,
    dispatch_uid='callbacks.signals.hero._hero_change'
)


def _hero_attribute_change(hero, equip_ids, **kwargs):
    this_hero = get_cache_hero(hero)
    for eid in equip_ids:
        add_extra_attr_to_hero(this_hero, eid)

    cache.set('hero:{0}'.format(this_hero.id), this_hero)

    hero_changed_signal.send(
        sender=None,
        cache_hero_obj=this_hero
    )


socket_changed_signal.connect(
    _hero_attribute_change,
    dispatch_uid='core.cache._hero_attribute_change'
)



