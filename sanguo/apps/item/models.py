from django.db import models
from django.db.models.signals import post_delete, post_save

from apps.item.cache import (delete_cache_equipment,
                             save_cache_equipment)
from core.mongoscheme import MongoChar
from core.signals import (equip_add_signal, equip_changed_signal,
                          equip_del_signal)

def encode_random_attrs(attrs):
    # attrs: [{1: {value: x, is_percent: y}}, ...]
    # serialize to: '1,x,y|2,x,y...'
    def _encode(attr):
        if not attr:
            return ''
        
        k, v = attr.items()[0]
        return '{0},{1},{2}'.format(
            k,
            int(v['value']),
            '1' if v['is_percent'] else '0'
        )
    
    data = [_encode(attr) for attr in attrs]
    return '|'.join(data)


def decode_random_attr(text):
    if not text:
        return []
    def _decode(t):
        _id, value, is_percent = t.split(',')
        data = {
            int(_id): {
                'value': int(value),
                'is_percent': is_percent == '1'
            }
        }
        return data
    
    res = [_decode(t) for t in text.split('|')]
    return res


class Equipment(models.Model):
    char_id = models.IntegerField()
    tp = models.SmallIntegerField()
    quality = models.SmallIntegerField()
    name = models.CharField(max_length=16)
    
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    
    base_value = models.IntegerField()
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
        return int(self.base_value * self.modulus)
    
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
