from core import GLOBAL
from core.mongoscheme import MongoChar
from core.exception import SanguoViewException

def save_gem(gems, char_id):
    from core.notify import add_gem_notify, update_gem_notify
    char = MongoChar.objects.only('gems').get(id=char_id)
    old_gems = char.gems
    
    gems_dict = {}
    for gid, amount in gems:
        gems_dict[gid] = gems_dict.get(gid, 0) + amount
    
    gems = gems_dict.items()
    
    new_gems = []
    update_gems = []
    for gid, amount in gems:
        gid = str(gid)
        if gid in old_gems:
            old_gems[gid] += amount
            
            update_gems.append((int(gid), old_gems[gid]))
        else:
            old_gems[gid] = amount
            new_gems.append((int(gid), amount))
    
    char.gems = old_gems
    char.save()
    
    if new_gems:
        add_gem_notify('noti:{0}'.format(char_id), new_gems)
    if update_gems:
        update_gem_notify('noti:{0}'.format(char_id), gems=update_gems)


def delete_gem(_id, _amount, char_id):
    from core.notify import update_gem_notify, remove_gem_notify
    
    char = MongoChar.objects.only('gems').get(id=char_id)
    this_gem_amount = char.gems[str(_id)]
    new_amount = this_gem_amount - _amount
    
    if new_amount < 0:
        raise Exception("delete_gem, error")
    if new_amount == 0:
        char.gems.pop(str(_id))
        char.save()
        remove_gem_notify('noti:{0}'.format(char_id), _id)
    else:
        char.gems[str(_id)] = new_amount
        char.save()
        update_gem_notify('noti:{0}'.format(char_id), [(_id, new_amount)])


def merge_gem(_id, _amount, using_sycee, char_id):
    from core.notify import add_gem_notify, update_gem_notify
    condition = GLOBAL.GEM[_id]['merge_condition']
    print "merge_gem,", _id, _amount, condition
    # FIXME
    
    condition_dict = {}
    for gid in condition:
        condition_dict[gid] = condition_dict.get(gid, 0) + 1

    char = MongoChar.objects.only('gems').get(id=char_id)
    for gid, amount in condition_dict.iteritems():
        if char.gems.get(str(gid), 0) < amount * _amount:
            raise SanguoViewException(600)
    
    update_gems = []
    for gid, amount in condition_dict.iteritems():
        char.gems[str(gid)] -= amount
        
        update_gems.append( (gid, char.gems[str(gid)]) )
    
    if str(_id) in char.gems:
        notify_method = update_gem_notify
    else:
        notify_method = add_gem_notify
    
    char.gems[str(_id)] = char.gems.get(str(_id), 0) + _amount
    _amount = char.gems[str(_id)]
    
    char.save()
    
    notify_method('noti:{0}'.format(char_id), [(_id, _amount)])
    
