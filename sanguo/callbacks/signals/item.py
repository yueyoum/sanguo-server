from core.signals import (
    equip_add_signal,
    equip_changed_signal,
    equip_del_signal,
    
    gem_changed_signal,
    gem_add_signal,
    gem_del_signal,
    
    socket_changed_signal,
)


from core.notify import (
    add_equipment_notify,
    update_equipment_notify,
    remove_equipment_notify,
    
    add_gem_notify,
    update_gem_notify,
    remove_gem_notify,
)

from core.formation import find_socket_by_equip
from core import GLOBAL

EQUIP_TEMPLATE = GLOBAL.EQUIP.EQUIP_TEMPLATE

def _equip_add(cache_equip_obj, **kwargs):
    add_equipment_notify(
        cache_equip_obj.char_id,
        cache_equip_obj
    )


def _equip_changed(cache_equip_obj, **kwargs):
    update_equipment_notify(
        cache_equip_obj.char_id,
        cache_equip_obj
    )
    
    equip_id = int(cache_equip_obj.id)
    
    socket = find_socket_by_equip(
        cache_equip_obj.char_id,
        equip_id
        )

    if socket and socket.hero:
        tp = EQUIP_TEMPLATE[cache_equip_obj.tid]['tp']
        kwargs = {
            'hero': socket.hero,
            'weapon': 0,
            'armor': 0,
            'jewelry': 0
        }
        if tp == 1:
            kwargs['weapon'] = equip_id
        elif tp == 2:
            kwargs['jewelry'] = equip_id
        else:
            kwargs['armor'] = equip_id
        
        socket_changed_signal.send(sender=None, **kwargs)
    
    

def _equip_del(char_id, equip_id, **kwargs):
    remove_equipment_notify(
        char_id,
        equip_id
    )


def _gem_changed(char_id, gems, **kwargs):
    update_gem_notify(
        char_id,
        gems
    )

def _gem_add(char_id, gems, **kwargs):
    add_gem_notify(
        char_id,
        gems
    )


def _gem_del(char_id, gid, **kwargs):
    if gid:
        remove_gem_notify(
            char_id,
            gid
        )
    


equip_add_signal.connect(
    _equip_add,
    dispatch_uid = 'core.callbacks.item._equip_add'
)

equip_changed_signal.connect(
    _equip_changed,
    dispatch_uid = 'core.callbacks.item._equip_changed'
)

equip_del_signal.connect(
    _equip_del,
    dispatch_uid = 'core.callbacks.item._equip_del'
)



gem_changed_signal.connect(
    _gem_changed,
    dispatch_uid = 'core.callbacks.item._gem_changed'
)

gem_add_signal.connect(
    _gem_add,
    dispatch_uid = 'core.callbacks.item._gem_add'
)


gem_del_signal.connect(
    _gem_del,
    dispatch_uid = 'core.callbacks.item._gem_del'
)

