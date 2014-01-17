from core.signals import (
    equip_changed_signal,
    socket_changed_signal,
    )

from core.formation import Formation


def _equip_changed(char_id, equip_obj, **kwargs):
    equip_id = equip_obj.equip_id

    f = Formation(char_id)
    socket = f.find_socket_by_equip(equip_id)

    if socket:
        socket_changed_signal.send(
            sender=None,
            socket_obj=socket
        )


equip_changed_signal.connect(
    _equip_changed,
    dispatch_uid='core.callbacks.item._equip_changed'
)

