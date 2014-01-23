# -*- coding: utf-8 -*-
import random

from core.character import Char
from core.exception import SanguoException
from utils.decorate import message_response

from apps.hero.models import Hero as ModelHero



@message_response("MergeHeroResponse")
def merge_hero(request):
    req = request._proto
    char_id = request._char_id

    char = Char(char_id)
    in_bag_hero_ids = char.in_bag_hero_ids()

    using_hero_ids = req.using_hero_ids
    for i in using_hero_ids:
        if i not in in_bag_hero_ids:
            raise SanguoException(300)

    heros = char.heros_dict
    original_ids = []
    for i in using_hero_ids:
        original_ids.append(heros[i])

    all_heros = ModelHero.all()
    original_quality = [all_heros[hid].quality for hid in original_ids]

    if len(set(original_quality)) != 1:
        raise SanguoException(301)

    if len(using_hero_ids) == 2:
        target_quality = 1
        if original_quality[0] != 1:
            raise SanguoException(302)
    elif len(using_hero_ids) == 8:
        target_quality = original_quality[0] - 1
        if original_quality[0] == 1:
            raise SanguoException(302)
    else:
        raise SanguoException(302)

    all_heros = ModelHero.all()
    all_hero_ids = []
    for h in all_heros.values():
        if h.quality == target_quality:
            all_hero_ids.append(h.id)

    if original_quality[0] == 1:
        while True:
            choosing_id = random.choice(all_hero_ids)
            if choosing_id not in original_ids:
                break
    else:
        choosing_id = random.choice(all_hero_ids)

    char.delete_hero(using_hero_ids)
    char.save_hero(choosing_id)

    return None
