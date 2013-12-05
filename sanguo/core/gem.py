from core import GLOBAL
from core.mongoscheme import MongoChar
from core.exception import SanguoViewException

from core.signals import (
    gem_changed_signal,
    gem_add_signal,
    gem_del_signal,
)

def save_gem(gems, char_id):
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
        gem_add_signal.send(
            sender = None,
            char_id = char_id,
            gems = new_gems
        )
    if update_gems:
        gem_changed_signal.send(
            sender = None,
            char_id = char_id,
            gems = update_gems
        )


def delete_gem(_id, _amount, char_id):
    char = MongoChar.objects.only('gems').get(id=char_id)
    this_gem_amount = char.gems[str(_id)]
    new_amount = this_gem_amount - _amount
    
    if new_amount < 0:
        raise Exception("delete_gem, error")
    if new_amount == 0:
        char.gems.pop(str(_id))
        char.save()
        gem_del_signal.send(
            sender = None,
            char_id = char_id,
            gid = _id
        )
    else:
        char.gems[str(_id)] = new_amount
        char.save()
        gem_changed_signal.send(
            sender = None,
            char_id = char_id,
            gems = [(_id, new_amount)]
        )


def merge_gem(_id, _amount, using_sycee, char_id):
    condition = GLOBAL.GEM[_id]['merge_condition']
    print "merge_gem,", _id, _amount, condition
    # FIXME
    # TODO using_sycee
    
    condition_dict = {}
    for gid in condition:
        condition_dict[gid] = condition_dict.get(gid, 0) + 1

    char = MongoChar.objects.only('gems').get(id=char_id)
    for gid, amount in condition_dict.iteritems():
        if char.gems.get(str(gid), 0) < amount * _amount:
            raise SanguoViewException(600)
    
    update_gems = []
    remove_gems = []
    new_gem = []
    for gid, amount in condition_dict.iteritems():
        char.gems[str(gid)] -= amount * _amount
        
        if char.gems[str(gid)] == 0:
            char.gems.pop(str(gid))
            remove_gems.append(gid)
        else:
            update_gems.append( (gid, char.gems[str(gid)]) )
    
    if str(_id) in char.gems:
        char.gems[str(_id)] += 1
        update_gems.append( (_id, char.gems[str(_id)]) )
    else:
        char.gems[str(_id)] = _amount
        new_gem = [(_id, _amount)]
    
    char.save()
    
    gem_changed_signal.send(
        sender = None,
        char_id = char_id,
        gems = update_gems
    )
    
    gem_add_signal.send(
        sender = None,
        char_id = char_id,
        gems = new_gem
    )
    
    gem_del_signal.send(
        sender = None,
        char_id = char_id,
        gid = remove_gems
    )
