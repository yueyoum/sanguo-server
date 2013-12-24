from utils import cache

def save_cache_character(model_obj):
    cache.set(
        'char:{0}'.format(model_obj.id),
        model_obj
        )
    return model_obj



def get_cache_character(_id):
    c = cache.get('char:{0}'.format(_id))
    if c:
        return c
    
    
    from apps.character.models import Character
    try:
        model_obj = Character.objects.get(id=_id)
    except Character.DoesNotExist:
        return None
    save_cache_character(model_obj)
    
    return model_obj

