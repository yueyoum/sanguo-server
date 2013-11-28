# -*- coding: utf-8 -*-

import random
import json
from _base import data_path

# 1 武器， 2 饰品， 3 防具
# 1 白 2 绿 3 蓝 4 紫

_TP_NAME = {
        1: 'attack',
        2: 'hp',
        3: 'defense',
        }


def get_equip_level_step(level):
    if level < 30:
        return 0
    if level < 60:
        return 30
    if level < 90:
        return 60
    return 90


def load_equip_template():
    # {
    #     id: {tp: , quality: name;,  fixed:}
    # }

    with open(data_path('equip_template.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        fields = c['fields']
        fields.pop('des')
        name = fields.pop('name')
        fields['name'] = [n.strip() for n in name.split(',')]

        data[c['pk']] = fields

    return data

def load_equip_level_info():
    # {
    #     level: {
    #             attack: ,
    #             hp: ,
    #             defense: ,
    #             cost: ,
    #             exp: ,
    #             quality: {
    #                     1:  {
    #                             exp:,
    #                             gold:,
    #                         },
    #                     2:,
    #                     3:,
    #                     4:
    #                 }
    #         }
    # }


    with open(data_path('equip_level_info.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        fields = c['fields']
        quality = {
                1: {
                    'exp':  fields['white_exp'],
                    'gold': fields['white_gold']
                    },
                2: {
                    'exp':  fields['green_exp'],
                    'gold': fields['green_gold']
                    },
                3: {
                    'exp':  fields['blue_exp'],
                    'gold': fields['blue_gold']
                    },
                4: {
                    'exp':  fields['purple_exp'],
                    'gold': fields['purple_gold']
                    },
                }

        data[c['pk']] = {
                'attack': fields['attack'],
                'hp': fields['hp'],
                'defense': fields['defense'],
                'cost': fields['cost'],
                'exp': fields['exp'],
                'quality': quality
                }

    return data


def load_equip_level_range_info():
    # {
    #     level_step: {
    #             1: [a, b],
    #             2: ,
    #             3: ,
    #             modulus: {
    #                     1: ,
    #                     2: ,
    #                     3: ,
    #                     4: ,
    #                 }
    #         }        
    # }


    with open(data_path('equip_level_range_info.json'), 'r') as f:
        content = json.loads(f.read())

    def _parse(text):
        a, b = text.split(',')
        return int(a), int(b) + 1

    data = {}
    for c in content:
        fields = c['fields']
        m = fields['modulus']

        data[fields['level']] = {
                1: _parse(fields['attack']),
                2: _parse(fields['hp']),
                3: _parse(fields['defense']),
                'modulus': {
                    1: m * fields['white_modulus'],
                    2: m * fields['green_modulus'],
                    3: m * fields['blue_modulus'],
                    4: m * fields['purple_modulus'],
                    }
                }
    return data


def load_random_attribute():
    # {
    #     id: {
    #             is_percent:
    #             0:,
    #             30:,
    #             60:,
    #             90:,
    #             change_value_is_percent:
    #             change_value:,
    #             used_for:,
    #             effect:
    #         }        
    # }


    with open(data_path('equip_random_attribute.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        fields = c['fields']

        fields[0]  = fields.pop('level_zero')
        fields[30] = fields.pop('level_one')
        fields[60] = fields.pop('level_two')
        fields[90] = fields.pop('level_three')

        data[c['pk']] = fields

    return data



EQUIP_TEMPLATE = load_equip_template()
EQUIP_LEVEL_INFO = load_equip_level_info()
EQUIP_LEVEL_RANGE_INFO = load_equip_level_range_info()
EQUIP_RANDOM_ATTRIBUTE = load_random_attribute()

_EXP_LEVEL = [(v['exp'], k) for k, v in EQUIP_LEVEL_INFO.iteritems()]
_EXP_LEVEL.sort(key=lambda item: item[0])

def get_level_by_exp(exp):
    # FIXME 满级
    for e, l in _EXP_LEVEL:
        if e > exp:
            return l



_RANDOM_ATTRS = {
        1: [],
        2: [],
        3: [],
        }

for k, v in EQUIP_RANDOM_ATTRIBUTE.iteritems():
    _RANDOM_ATTRS[v['used_for']].append(k)

def get_random_attributes(tp, level):
    # 先根据类型和等级范围确定随机属性的数量
    level_step = get_equip_level_step(level)
    number_range = EQUIP_LEVEL_RANGE_INFO[level_step][tp]
    number_of_attrs = random.choice(range(*number_range))

    base_attr_ids = _RANDOM_ATTRS[tp][:]
    if not base_attr_ids:
        return []

    res = []
    while True:
        if len(res) >= number_of_attrs or not base_attr_ids:
            break

        attr_id = random.choice(base_attr_ids)
        base_attr_ids.remove(attr_id)

        if attr_id not in res:
            res.append(attr_id)

    # 再根据等级范围确定选出的每个属性的数值
    final = []
    for attr_id in res:
        base_value = EQUIP_RANDOM_ATTRIBUTE[attr_id][level_step]
        is_percent = EQUIP_RANDOM_ATTRIBUTE[attr_id]['is_percent']
        change_value = EQUIP_RANDOM_ATTRIBUTE[attr_id]['change_value']
        change_value_is_percent = EQUIP_RANDOM_ATTRIBUTE[attr_id]['change_value_is_percent']
        if is_percent:
            if change_value_is_percent:
                value = base_value + random.randint(0, change_value)
            else:
                raise Exception("value is percent, but change value is not precent")
        else:
            if change_value_is_percent:
                change_value = random.randint(0, change_value)
                value = base_value * (1 + change_value)
            else:
                value = base_value + random.randint(0, change_value)

        final.append( {attr_id: {'value': value, 'is_percent': is_percent}} )

    return final



def generate_equip(tid, level):
    if level == 1:
        exp = 0
    else:
        exp = EQUIP_LEVEL_INFO[level-1]['exp']

    template = EQUIP_TEMPLATE[tid]
    tp = template['tp']
    quality = template['quality']
    name = random.choice(template['name'])

    extra = get_random_attributes(tp, level)

    base_value = EQUIP_LEVEL_INFO[level][_TP_NAME[tp]]
    hole_amount = len(extra)

    level_step = get_equip_level_step(level)
    modulus = EQUIP_LEVEL_RANGE_INFO[level_step]['modulus'][quality]

    return {
            'tid': tid,
            'name': name,
            'level': level,
            'exp': exp,
            'base_value': base_value,
            'modulus': modulus,
            'hole_amount': hole_amount,
            'random_attrs': extra
            }

