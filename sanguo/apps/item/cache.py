from utils import cache



def save_cache_equipment(model_obj):
    cache.set(
        'equip:{0}'.format(model_obj.id),
        model_obj
    )
    return model_obj
    

def delete_cache_equipment(model_obj):
    cache.delete('equip:{0}'.format(model_obj.id))


def get_cache_equipment(_id):
    e = cache.get('equip:{0}'.format(_id))
    if e:
        return e

    from apps.item.models import Equipment
    model_obj = Equipment.objects.get(id=_id)
    
    save_cache_equipment(model_obj)
    return model_obj
    
