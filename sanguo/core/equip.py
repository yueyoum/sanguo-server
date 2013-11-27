from core.drives import  document_ids
from core import GLOBAL

EQUIP = GLOBAL.EQUIP.EQUIP
EQUIP_LEVEL_INFO = GLOBAL.EQUIP.EQUIP_LEVEL_INFO
EQUIP_LEVEL_RANGE_INFO = GLOBAL.EQUIP.EQUIP_LEVEL_RANGE_INFO

get_equip_level_step = GLOBAL.EQUIP.get_equip_level_step
get_level_by_exp = GLOBAL.EQUIP.get_level_by_exp


_TP_NAME = {
        1: 'attack',
        2: 'hp',
        3: 'defense',
        }

def save_equip(data, char_id, equip_id=None):
    if not equip_id:
        equip_id = document_ids.inc('equip')
    pass



def _calculate(level, quality, tp, extra):
    tp_name = _TP_NAME[tp]

    attrs = {
            'attack': 0,
            'hp': 0,
            'defense': 0,
            }

    value = EQUIP_LEVEL_INFO[level][tp_name]
    level_step = get_equip_level_step(level)
    modulus = EQUIP_LEVEL_RANGE_INFO[level_step]['modulus'][quality]

    value *= modulus

    attrs[tp_name] = value
    attrs['extra'] = extra

    return attrs

#def calculate(_id):
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

