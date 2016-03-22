from core.signals import (
    equip_changed_signal,
    socket_changed_signal,
    stuff_add_signal,
    stuff_remove_signal,
    )

from core.formation import Formation
from core.activity import ActivityStatic


def _equip_changed(char_id, equip_obj, **kwargs):
    equip_id = equip_obj.equip_id

    f = Formation(char_id)
    socket = f.find_socket_by_equip(equip_id)

    if socket:
        socket_changed_signal.send(
            sender=None,
            socket_obj=socket
        )


def _stuff_add(char_id, stuff_id, add_amount, new_amount, **kwargs):
    if stuff_id == 3003:
        ActivityStatic(char_id).trig(7001)
    elif stuff_id == 3014:
        ActivityStatic(char_id).trig(18009)


def _stuff_remove(char_id, stuff_id, rm_amount, new_amount, **kwargs):
    if stuff_id == 3003:
        ActivityStatic(char_id).trig(7001)
    elif stuff_id == 3014:
        ActivityStatic(char_id).trig(18009)


equip_changed_signal.connect(
    _equip_changed,
    dispatch_uid='core.callbacks.item._equip_changed'
)

stuff_add_signal.connect(
    _stuff_add,
    dispatch_uid='callbacks.signal.item._stuff_add'
)

stuff_remove_signal.connect(
    _stuff_remove,
    dispatch_uid='callbacks.signal.item._stuff_remove'
)
