from redisco import models

from core.mongoscheme import MongoChar

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



class CacheEquipment(models.Model):
    char_id = models.IntegerField(indexed=False, required=True)
    tid = models.IntegerField(indexed=False, required=True)
    name = models.CharField(indexed=False, required=True)
    level = models.IntegerField(indexed=False, required=True)
    exp = models.IntegerField(indexed=False, required=True)
    
    base_value = models.IntegerField(indexed=False, required=True)
    modulus = models.FloatField(indexed=False, required=True)
    hole_amount = models.IntegerField(indexed=False, required=True)
    hole_opened = models.IntegerField(indexed=False, required=True)
    gem_ids = models.CharField(indexed=False, required=False)
    random_attrs = models.CharField(indexed=False, required=False)
    
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
    def gems(self):
        if not self.gem_ids:
            return []
        return [int(i) for i in self.gem_ids.split(',')]


def save_cache_equipment(model_obj):
    MongoChar.objects(id=model_obj.char_id).update_one(
        add_to_set__equips = model_obj.id
    )
    #try:
    #    mc = MongoChar.objects.only('equips').get(id=model_obj.char_id)
    #except DoesNotExist:
    #    mc = MongoChar()
    #    mc.id = model_obj.char_id
    #if model_obj.id not in mc.equips:
    #    mc.equips.append(model_obj.id)
    #    mc.save()
    
    e = CacheEquipment.objects.get_by_id(model_obj.id)
    if e is None:
        e = CacheEquipment()
        e.id = model_obj.id
    
    for attr in e.attributes_dict:
        setattr(e, attr, getattr(model_obj, attr))
    
    res = e.save()
    if res is not True:
        raise Exception(str(res))
    return e
    
    

def delete_cache_equipment(model_obj):
    MongoChar.objects(id=model_obj.char_id).update_one(
        pull__equips = model_obj.id
    )
    
    e = CacheEquipment.objects.get_by_id(model_obj.id)
    if e:
        print "CacheEquipment, cahce delete!!!"
        e.delete()


def get_cache_equipment(_id):
    e = CacheEquipment.objects.get_by_id(_id)
    if e:
        print "CacheEquipment, cahce hit!!!"
        return e

    from apps.item.models import Equipment
    model_obj = Equipment.objects.get(id=_id)
    
    e = save_cache_equipment(model_obj)
    return e
    
    