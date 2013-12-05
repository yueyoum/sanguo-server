from django.db import models
from django.db.models.signals import post_delete, post_save

from apps.item.cache import save_cache_equipment, delete_cache_equipment
from core.signals import (
    equip_add_signal,
    equip_changed_signal,
    equip_del_signal,
    )

from core.mongoscheme import MongoChar


class Equipment(models.Model):
    char_id = models.IntegerField()
    tid = models.IntegerField()
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
