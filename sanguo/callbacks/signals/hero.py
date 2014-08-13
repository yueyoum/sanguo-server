from core.signals import (
    hero_add_signal,
    hero_del_signal,
    hero_changed_signal,
    hero_step_up_signal,
    hero_to_soul_signal,
    socket_changed_signal,
    )

from core.notify import (
    add_hero_notify,
    remove_hero_notify,
    update_hero_notify,
    )

from core.character import Char
from core.hero import Hero, char_heros_dict
from core.achievement import Achievement
from preset.data import HEROS
from preset.settings import HERO_MAX_STEP

from protomsg import HeroToSoulNotify

from utils import pack_msg
from core.msgpipe import publish_to_char


def _hero_add(char_id, hero_ids, hero_original_ids, send_notify, **kwargs):
    if send_notify:
        heros = [Hero.cache_obj(i) for i in hero_ids]
        add_hero_notify(char_id, heros)

    heros_dict = char_heros_dict(char_id)

    achievement = Achievement(char_id)
    achievement.trig(1, len(heros_dict), send_notify=send_notify)

    quality_one_heros_amount = 0
    quality_two_heros_amount = 0
    quality_three_heros_amount = 0
    gender_female_heros_amount = 0


    for h in heros_dict.values():
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

def _hero_del(char_id, hero_ids, **kwargs):
    remove_hero_notify(char_id, hero_ids)


def _hero_change(hero_id, **kwargs):
    hero = Hero(hero_id)
    hero.save_cache()

    update_hero_notify(
        hero.char_id,
        [hero,]
    )
    
    Char(hero.char_id).send_notify()

def _hero_to_soul(char_id, souls, **kwargs):
    for _id, _amount in souls:
        msg = HeroToSoulNotify()
        msg.hero_id = _id
        msg.soul_amount = _amount
        publish_to_char(char_id, pack_msg(msg))


def _hero_step_up(char_id, hero_id, new_step, **kwargs):
    achievement = Achievement(char_id)
    achievement.trig(20, 1)
    if new_step == HERO_MAX_STEP:
        achievement.trig(21, 1)

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

hero_step_up_signal.connect(
    _hero_step_up,
    dispatch_uid='callbacks.signals.hero._hero_step_up'
)

hero_to_soul_signal.connect(
    _hero_to_soul,
    dispatch_uid='callbacks.signals.hero._hero_to_soul'
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



