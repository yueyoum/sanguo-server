from django.db import models
from django.db.models.signals import post_delete, post_save

from apps.item.cache import save_cache_equipment, delete_cache_equipment

class Equipment(models.Model):
    char_id = models.IntegerField()
    tid = models.IntegerField()
    name = models.CharField(max_length=16)
    
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    
    base_value = models.IntegerField()
    modulus = models.FloatField()
    hole_amount = models.IntegerField()
    
    random_attrs = models.CharField(max_length=255)

    def __unicode__(self):
        return u'<Equipment %d: %s, %d>' % (
            self.id, self.name, self.level
        )
    
    class Meta:
        db_table = 'equipment'


def equipment_save_callback(sender, instance, **kwargs):
    save_cache_equipment(instance)

def equipment_delete_callback(sender, instance, **kwargs):
    delete_cache_equipment(instance)


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
