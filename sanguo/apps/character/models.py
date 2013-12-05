from django.db import models
from django.db.models.signals import post_delete, post_save

from apps.character.cache import save_cache_character, delete_cache_character

class Character(models.Model):
    account_id = models.IntegerField(db_index=True)
    server_id = models.IntegerField(db_index=True)
    
    name = models.CharField(max_length=10)
    gold = models.IntegerField(default=0)
    sycee = models.IntegerField(default=0)
    
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    official = models.IntegerField(default=0)
    honor = models.IntegerField(default=0)


    def __unicode__(self):
        return u'<Character %d:%d:%d, %s>' % (
                self.account_id, self.server_id, self.id, self.name
                )
    
    class Meta:
        db_table = 'char_'
        unique_together = (
                ('account_id', 'server_id'),
                ('server_id', 'name'),
                )
    
    

def character_save_callback(sender, instance, **kwargs):
    save_cache_character(instance)

def character_delete_callback(sender, instance, **kwargs):
    delete_cache_character(instance.id)

post_save.connect(
    character_save_callback,
    sender = Character,
    dispatch_uid = 'apps.character.Character.post_save'
)

post_delete.connect(
    character_delete_callback,
    sender = Character,
    dispatch_uid = 'apps.character.Character.post_delete'
)


