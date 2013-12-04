from redisco import models

class CacheCharacter(models.Model):
    account_id = models.IntegerField(indexed=False, required=True)
    server_id = models.IntegerField(indexed=False, required=True)
    
    name = models.CharField(indexed=False, required=True)
    gold = models.IntegerField(indexed=False, required=True)
    gem = models.IntegerField(indexed=False, required=True)
    level = models.IntegerField(indexed=False, required=True)
    exp = models.IntegerField(indexed=False, required=True)
    official = models.IntegerField(indexed=False, required=True)
    honor = models.IntegerField(indexed=False, required=True)


def save_cache_character(model_obj):
    c = CacheCharacter.objects.get_by_id(model_obj.id)
    if c is None:
        c = CacheCharacter()
        c.id = model_obj.id
    
    for attr in c.attributes_dict:
        setattr(c, attr, getattr(model_obj, attr))
    
    res = c.save()
    if res is not True:
        raise Exception(str(res))
    return c


def delete_cache_character(_id):
    c = CacheCharacter.objects.get_by_id(_id)
    if c:
        c.delete()


def get_cache_character(_id):
    c = CacheCharacter.objects.get_by_id(_id)
    if c:
        return c
    
    from apps.character.models import Character
    model_obj = Character.objects.get(id=_id)
    
    c = save_cache_character(model_obj)
    return c

def get_multi_cache_characters(id_list):
    none_exists_id = False
    res = []
    for _id in id_list:
        c = CacheCharacter.objects.get_by_id(_id)
        if not c:
            none_exists_id = True
            break
        
        res.append(c)
    
    if not none_exists_id:
        return res
    
    from apps.character.models import Character
    objs = Character.objects.filter(id__in=id_list)
    
    res = []
    for obj in objs:
        c = save_cache_character(obj)
        res.append(c)
        
    return res
