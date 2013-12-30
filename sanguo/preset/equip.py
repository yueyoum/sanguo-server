# -*- coding: utf-8 -*-

import random
import json
from _base import data_path
from settings import EQUIP_LEVEL_RANGE, EQUIP_QUALITY_MODULUS

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
    #     id: {id:, tp: , quality: name;,  std:}
    # }

    with open(data_path('equip_template.json'), 'r') as f:
        content = json.loads(f.read())

    data = {}
    for c in content:
        fields = c['fields']
        fields.pop('des')
        name = fields.pop('name')
        fields['name'] = [n.strip() for n in name.split(',')]
        fields['id'] = c['pk']

        data[c['pk']] = fields

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

        fields[0] = fields.pop('level_zero')
        fields[30] = fields.pop('level_one')
        fields[60] = fields.pop('level_two')
        fields[90] = fields.pop('level_three')

        data[c['pk']] = fields

    return data


EQUIP_TEMPLATE = load_equip_template()
EQUIP_RANDOM_ATTRIBUTE = load_random_attribute()

_EQUIP_IDS_BY_QUALITY_ALL = {}
_EQUIP_IDS_BY_QUALITY_STD = {}


def EQUIP_IDS_BY_QUALITY(quality, only_std=False):
    global _EQUIP_IDS_BY_QUALITY_ALL
    global _EQUIP_IDS_BY_QUALITY_STD

    def _filter(e):
        _id, x = e
        if only_std:
            return x['std'] and x['quality'] == quality
        return x['quality'] == quality

    if only_std:
        if quality not in _EQUIP_IDS_BY_QUALITY_STD:
            filter_list = filter(_filter, EQUIP_TEMPLATE.items())
            _EQUIP_IDS_BY_QUALITY_STD[quality] = [k for k, v in filter_list]
        return _EQUIP_IDS_BY_QUALITY_STD[quality]

    if quality not in _EQUIP_IDS_BY_QUALITY_ALL:
        filter_list = filter(_filter, EQUIP_TEMPLATE.items())
        _EQUIP_IDS_BY_QUALITY_ALL[quality] = [k for k, v in filter_list]

    return _EQUIP_IDS_BY_QUALITY_ALL[quality]


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
    number_range = EQUIP_LEVEL_RANGE[level_step][tp]
    number_range[-1] += 1
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

        final.append((attr_id, value, is_percent))
        print 'final =', final

    return final


def generate_equip(tid, level):
    template = EQUIP_TEMPLATE[tid]
    tp = template['tp']
    quality = template['quality']
    name = random.choice(template['name'])

    extra = get_random_attributes(tp, level)

    hole_amount = len(extra)

    level_step = get_equip_level_step(level)
    modulus = EQUIP_LEVEL_RANGE[level_step]['modulus'] * EQUIP_QUALITY_MODULUS[quality]
    modulus *= random.uniform(1, 1.08)

    #FIXME
    return {
        'tp': tp,
        'quality': quality,
        'name': name,
        'level': level,
        'modulus': modulus,
        'hole_amount': hole_amount,
        'random_attrs': extra
    }

