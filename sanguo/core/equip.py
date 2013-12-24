# -*- coding: utf-8 -*-

from apps.item.cache import get_cache_equipment
from apps.item.models import encode_random_attrs, Equipment
from core import GLOBAL
from core.gem import save_gem, delete_gem
from core.signals import equip_changed_signal
from core.exception import InvalidOperate
from core.character import Char

generate_equip = GLOBAL.EQUIP.generate_equip


class EquipUpdateProcess(object):
    __slots__ = ['processes', ]
    def __init__(self):
        self.processes = []
    
    def __iter__(self):
        for p in self.processes:
            yield p
    
    
    def add(self, data):
        self.processes.append(data)
    
    @property
    def end(self):
        end = self.processes[-1]
        return end[0], end[1]


class Equip(object):
    def __init__(self, lv, tp, quality):
        self.tp = tp
        self.lv = lv
        self.quality = quality

    def value(self):
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


    def update_needs_exp(self, lv):
        exp = int(round(pow(lv, 2.5) + lv * 100, -2))
        return exp

    def whole_exp(self):
        _exp = 0
        for i in range(self.lv-1, 0, -1):
            _exp += self.update_needs_exp(i)
        return _exp

    def update_process(self, current_exp, input_exp):
        # 并不是真正的升级，只是计算升级后的等级和经验
        p = EquipUpdateProcess()
        exp = current_exp + input_exp
        start_lv = self.lv
        lv = self.lv

        while True:
            need_exp = self.update_needs_exp(lv)
            if exp < need_exp:
                break

            lv += 1
            exp -= need_exp

        p.add((start_lv, current_exp, self.update_needs_exp(start_lv)))
        for i in range(start_lv+1, lv):
            p.add((i, 0, self.update_needs_exp(i)))

        p.add((lv, exp, self.update_needs_exp(lv)))
        return p


    def worth_exp(self):
        # 此装备值多少经验，被吞噬，能提供多少经验
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
        # 能卖多少金币
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



def embed_gem(char_id, equip_id, hole_id, gem_id):
    # gem_id = 0 表示取下hole_id对应的宝石
    if gem_id:
        message_name = "EmbedGemResponse"
    else:
        message_name = "UnEmbedGemResponse"
    
    char = Char(char_id)
    char_gems = char.gems
    char_equip_ids = char.equip_ids
    
    if equip_id not in char_equip_ids:
        raise InvalidOperate(message_name)
    
    if gem_id and gem_id not in char_gems:
        raise InvalidOperate(message_name)

    cache_equip = get_cache_equipment(equip_id)
    gems = cache_equip.gems
    
    hole_index = hole_id - 1
    
    try:
        off_gem = int(gems[hole_index])
        gems[hole_index] = str(gem_id)
    except KeyError:
        raise InvalidOperate(message_name)
    
    
    if gem_id:
        # 镶嵌
        delete_gem(gem_id, 1, char_id)
        if off_gem:
            save_gem([(off_gem, 1)], char_id)
    else:
        # 去下
        if not off_gem:
            raise InvalidOperate(message_name)
        
        save_gem([(off_gem, 1)], char_id)


    equip = Equipment.objects.get(id=equip_id)
    equip.gem_ids = ','.join(gems)
    equip.save()
