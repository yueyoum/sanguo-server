# -*- coding: utf-8 -*-

from core import GLOBAL
from apps.item.cache import encode_random_attrs, get_cache_equipment
from apps.item.models import Equipment
from core.gem import save_gem
from core.signals import (
    equip_changed_signal,
    )

EQUIP_TEMPLATE = GLOBAL.EQUIP.EQUIP_TEMPLATE
EQUIP_LEVEL_INFO = GLOBAL.EQUIP.EQUIP_LEVEL_INFO
EQUIP_LEVEL_RANGE_INFO = GLOBAL.EQUIP.EQUIP_LEVEL_RANGE_INFO

get_equip_level_step = GLOBAL.EQUIP.get_equip_level_step
get_level_by_exp = GLOBAL.EQUIP.get_level_by_exp
generate_equip = GLOBAL.EQUIP.generate_equip

_TP_NAME = GLOBAL.EQUIP._TP_NAME

_LEVEL_LIST = EQUIP_LEVEL_INFO.keys()
_LEVEL_LIST.sort()
_LEVEL_EXP_LIST = [(l, EQUIP_LEVEL_INFO[l]['exp']) for l in _LEVEL_LIST]


class EquipAttr(object):
    def __init__(self, tp, lv, quality):
        self.tp = tp
        self.lv = lv
        self.quality = quality


    def main_attr(self):
        score_base_ratio = 0.7      # 基础属性比例

        # 类型区别
        tp_base = {
                1: 0.4,
                2: 0.3,
                3: 0.3
                }
        tp_adjust = {
                1: 2.5,
                2: 1,
                3: 5
                }

        score = 70 * self.quality + self.lv * 90        # 基础70, 成长90
        value = score * score_base_ratio * tp_base[self.tp] * tp_adjust[self.tp]
        value = int(round(value))
        return value



    def level_required_exp(self, lv):
        exp = int(round(pow(lv, 2.5) + lv * 100, -2))
        return exp

    def whole_exp(self):
        _exp = 0
        for i in range(self.lv-1, 0, -1):
            _exp += self.level_required_exp(i)
        return _exp

    def update(self, current_total_exp, input_exp):
        whole_exp = self.whole_exp()
        exp = current_total_exp - whole_exp + input_exp
        lv = self.lv

        while True:
            need_exp = self.level_required_exp(lv)
            if need_exp > exp:
                break

            lv += 1
            exp -= need_exp

        return lv, current_total_exp + input_exp

        

    def worth_exp(self):
        if self.quality == 1:
            return self.lv * 100
        if self.quality == 2:
            return int(self.lv * 100 * 1.5)

        _exp = self.whole_exp()

        # 品质传承系数
        if self.quality == 3:
            return int(_exp * 0.6)
        return int(_exp * 0.85)

    def sell_value(self):
        gold = 100 * pow(self.lv, 0.5) + 100
        if self.quality == 2:
            gold *= 1.8
        else:
            gold = 1500 * pow(self.lv, 0.5) + 2000
            if self.quality == 1:
                gold *= 1.6

        if self.tp == 1:
            # 武器加价
            gold *= 1.2

        return int(gold)


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
    
    equip_changed_signal.send(
        sender = None,
        cache_equip_obj = cache_equip
    )
    
