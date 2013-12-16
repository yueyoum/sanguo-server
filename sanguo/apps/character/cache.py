from utils import cache

def save_cache_character(model_obj):
    cache.set(
        'char:{0}'.format(model_obj.id),
        model_obj
        )
    return model_obj


def delete_cache_character(_id):
    cache.delete('char:{0}'.format(_id))


def get_cache_character(_id):
    c = cache.get('char:{0}'.format(_id))
    if c:
        return c
    
    from apps.character.models import Character
    model_obj = Character.objects.get(id=_id)
    save_cache_character(model_obj)
    
    return model_obj

