from utils import cache

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
    
