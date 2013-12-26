# -*- coding: utf-8 -*-
import json
from django.db import models
from django.db.models.signals import post_delete, post_save

from apps.item.cache import (delete_cache_equipment,
                             save_cache_equipment)
from core.mongoscheme import MongoChar
from core.signals import (equip_add_signal, equip_changed_signal,
                          equip_del_signal)

from core import GLOBAL


TP_ATTR = {
    1: 'attack',
    2: 'hp',
    3: 'defense'
}

EXTAR_ATTR = {
    3: 'attack',
    5: 'defense',
    7: 'dodge',
    9: 'crit',
    14: 'hp'
}


def encode_random_attrs(attrs):
    # attrs: [(id, value, is_percent), ...]
    return json.dumps(attrs)


def decode_random_attr(text):
    if not text:
        return []
    return json.loads(text)


class Equipment(models.Model):
    char_id = models.IntegerField()
    tp = models.SmallIntegerField()
    quality = models.SmallIntegerField()
    name = models.CharField(max_length=16)
    
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    
    modulus = models.FloatField()
    hole_amount = models.IntegerField()
    gem_ids = models.CharField(max_length=255)
    
    random_attrs = models.CharField(max_length=255)

    def __unicode__(self):
        return u'<Equipment %d: %s, %d>' % (
            self.id, self.name, self.level
        )
    
    class Meta:
        db_table = 'equipment'
        
        
    @property
    def decoded_random_attrs(self):
        attrs = getattr(self, '_decoded_random_attrs', None)
        if not attrs:
            attrs = decode_random_attr(self.random_attrs)
            self._decoded_random_attrs = attrs
        return attrs
    
    @property
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

        score = 70 * self.quality + self.level * 90        # 基础70, 成长90
        value = score * score_base_ratio * tp_base[self.tp] / tp_adjust[self.tp]
        value *= self.modulus
        return int(round(value))
    
    @property
    def hole_opened(self):
        if not self.gem_ids:
            return 0
        return len(self.gem_ids.split(','))
    
    @property
    def gems(self):
        if not self.gem_ids:
            return []
        return [int(i) for i in self.gem_ids.split(',')]
    
    
    def active_attrs(self):
        attrs = [
            (TP_ATTR[self.tp], self.value, False)
        ]
        random_attrs = self.decoded_random_attrs
        for k, v, p in random_attrs:
            e = GLOBAL.EQUIP.EQUIP_RANDOM_ATTRIBUTE[k]['effect']
            attrs.append(
                (EXTAR_ATTR[e], v, p)
            )
        
        gems = self.gems
        for gid in gems:
            if not gid:
                continue
            g = GLOBAL.GEM[gid]
            attrs.append(
                (EXTAR_ATTR[g['used_for']], g['value'], g['is_percent'])
            )
        
        return attrs


def equipment_save_callback(sender, instance, created, **kwargs):
    MongoChar.objects(id=instance.char_id).update_one(
        add_to_set__equips = instance.id
    )

    cache_equip = save_cache_equipment(instance)
    if created:
        equip_add_signal.send(
            sender = None,
            cache_equip_obj = cache_equip
        )
    else:
        equip_changed_signal.send(
            sender = None,
            cache_equip_obj = cache_equip
        )

def equipment_delete_callback(sender, instance, **kwargs):
    MongoChar.objects(id=instance.char_id).update_one(
        pull__equips = instance.id
    )
    
    delete_cache_equipment(instance)
    equip_del_signal.send(
        sender = None,
        char_id = instance.char_id,
        equip_id = instance.id
    )


post_save.connect(
    equipment_save_callback,
    sender = Equipment,
    dispatch_uid = 'apps.item.Equipment.post_save'
)

post_delete.connect(
    equipment_delete_callback,
    sender = Equipment,
    dispatch_uid = 'apps.item.Equipment.post_delete'
)
