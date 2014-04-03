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

from core.hero import Hero
from core.character import Char
from core.achievement import Achievement
from preset.data import HEROS


def _hero_add(char_id, hero_ids, hero_original_ids, send_notify, **kwargs):
    if send_notify:
        heros = [Hero.cache_obj(i) for i in hero_ids]
        add_hero_notify(char_id, heros)

    char = Char(char_id)
    char_heros_dict = char.heros_dict

    achievement = Achievement(char_id)
    achievement.trig(1, len(char_heros_dict), send_notify=send_notify)

    quality_one_heros_amount = 0
    quality_two_heros_amount = 0
    quality_three_heros_amount = 0
    gender_female_heros_amount = 0


    for h in char_heros_dict.values():
        original_hero = HEROS[h.oid]
        if original_hero.quality == 1:
            quality_one_heros_amount += 1
        if original_hero.quality == 2:
            quality_two_heros_amount += 1
        if original_hero.quality == 3:
            quality_three_heros_amount += 1
        if original_hero.gender == 2:
            gender_female_heros_amount += 1

    achievement.trig(2, quality_one_heros_amount, send_notify=send_notify)
    achievement.trig(3, quality_two_heros_amount, send_notify=send_notify)
    achievement.trig(4, quality_three_heros_amount, send_notify=send_notify)
    achievement.trig(5, gender_female_heros_amount, send_notify=send_notify)

    for oid in hero_original_ids:
        achievement.trig(6, oid, send_notify=send_notify)



def _hero_del(char_id, hero_ids, **kwargs):
    remove_hero_notify(char_id, hero_ids)


def _hero_change(hero_id, **kwargs):
    hero = Hero(hero_id)
    hero.save_cache()

    update_hero_notify(
        hero.char_id,
        [hero,]
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


def _hero_attribute_change(socket_obj, **kwargs):
    if not socket_obj.hero:
        return

    _hero_change(socket_obj.hero)

    # hero = Hero(socket_obj.hero)
    # hero.save_cache()
    #
    # hero_changed_signal.send(
    #     sender=None,
    #     cache_hero_obj=hero
    # )


socket_changed_signal.connect(
    _hero_attribute_change,
    dispatch_uid='core.cache._hero_attribute_change'
)



