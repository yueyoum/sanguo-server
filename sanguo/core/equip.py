# -*- coding: utf-8 -*-

from core import GLOBAL
from apps.item.cache import encode_random_attrs, get_cache_equipment
from apps.item.models import Equipment
from core.gem import save_gem

EQUIP_LEVEL_INFO = GLOBAL.EQUIP.EQUIP_LEVEL_INFO
EQUIP_LEVEL_RANGE_INFO = GLOBAL.EQUIP.EQUIP_LEVEL_RANGE_INFO

get_equip_level_step = GLOBAL.EQUIP.get_equip_level_step
get_level_by_exp = GLOBAL.EQUIP.get_level_by_exp
generate_equip = GLOBAL.EQUIP.generate_equip

_TP_NAME = GLOBAL.EQUIP._TP_NAME

_LEVEL_LIST = EQUIP_LEVEL_INFO.keys()
_LEVEL_LIST.sort()
_LEVEL_EXP_LIST = [(l, EQUIP_LEVEL_INFO[l]['exp']) for l in _LEVEL_LIST]


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



def get_equip_level_by_whole_exp(exp):
    if exp < EQUIP_LEVEL_INFO[ _LEVEL_LIST[0] ]['exp']:
        return _LEVEL_LIST[0]
    if exp >= EQUIP_LEVEL_INFO[ _LEVEL_LIST[-2] ]['exp']:
        return _LEVEL_LIST[-1]

    for level, wexp in _LEVEL_EXP_LIST:
        if wexp > exp:
            return level
    

def embed_gem(char_id, equip_id, hole_id, gem_id):
    # gem_id = 0 表示取下hole_id对应的宝石
    from core.notify import update_equipment_notify
    from apps.character.cache import get_cache_character
    cache_equip = get_cache_equipment(equip_id)
    gems = cache_equip.gems
    
    hole_index = hole_id - 1
    
    off_gem = int(gems[hole_index])
    gems[hole_index] = str(gem_id)
    
    
    if gem_id:
        # 镶嵌
        if off_gem:
            save_gem([(off_gem, 1)], char_id)
    else:
        # 去下
        if not off_gem:
            raise Exception("embed_gem, XXX")
        
        save_gem([(off_gem, 1)], char_id)


    equip = Equipment.objects.get(id=equip_id)
    equip.gem_ids = ','.join(gems)
    equip.save()
    
    cache_equip = get_cache_equipment(equip_id)
    cache_char = get_cache_character(char_id)
    notify_key = cache_char.notify_key
    update_equipment_notify(notify_key, cache_equip)
    
    

#def _calculate(level, quality, tp, extra):
#    tp_name = _TP_NAME[tp]
#
#    attrs = {
#            'attack': 0,
#            'hp': 0,
#            'defense': 0,
#            }
#
#    value = EQUIP_LEVEL_INFO[level][tp_name]
#    level_step = get_equip_level_step(level)
#    modulus = EQUIP_LEVEL_RANGE_INFO[level_step]['modulus'][quality]
#
#    value *= modulus
#
#    attrs[tp_name] = value
#    attrs['extra'] = extra
#
#    return attrs
#
#def equip_calculate(_id):
#    equip = document_equip.get(_id)
#    meta_data = EQUIP[equip['oid']]
#
#    return _calculate(
#            equip['level'],
#            meta_data['quality'],
#            meta_data['tp'],
#            equip['extra']
#            )
#    
#
