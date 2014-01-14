# -*- coding: utf-8 -*-

from apps.item.cache import get_cache_equipment
from apps.item.models import  Equipment
from core import GLOBAL
from core.gem import save_gem, delete_gem
from core.exception import InvalidOperate
from core.character import Char

generate_equip = GLOBAL.EQUIP.generate_equip


def generate_and_save_equip(tid, level, char_id):
    data = generate_equip(tid, level)
    data['random_attrs'] = encode_random_attrs(data['random_attrs'])
    data['char_id'] = char_id

    # FIXME
    data['gem_ids'] = ','.join(['0'] * data['hole_amount'])

    equip = Equipment.objects.create(**data)
    return get_cache_equipment(equip.id)


def delete_equip(_id):
    if isinstance(_id, (list, tuple)):
        ids = _id
    else:
        ids = [_id]
    Equipment.objects.filter(id__in=ids).delete()


def embed_gem(char_id, equip_id, hole_id, gem_id):
    # gem_id = 0 表示取下hole_id对应的宝石


    char = Char(char_id)
    char_gems = char.gems
    char_equip_ids = char.equip_ids

    if equip_id not in char_equip_ids:
        raise InvalidOperate()

    if gem_id and gem_id not in char_gems:
        raise InvalidOperate()

    cache_equip = get_cache_equipment(equip_id)
    gems = cache_equip.gems

    hole_index = hole_id - 1

    try:
        off_gem = int(gems[hole_index])
        gems[hole_index] = str(gem_id)
    except KeyError:
        raise InvalidOperate()

    if gem_id:
        # 镶嵌
        delete_gem(gem_id, 1, char_id)
        if off_gem:
            save_gem([(off_gem, 1)], char_id)
    else:
        # 去下
        if not off_gem:
            raise InvalidOperate()

        save_gem([(off_gem, 1)], char_id)

    equip = Equipment.objects.get(id=equip_id)
    equip.gem_ids = ','.join(gems)
    equip.save()
