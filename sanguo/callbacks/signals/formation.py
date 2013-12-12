from core.signals import formation_changed_signal

from core.notify import formation_notify

def _formation_changed(char_id, socket_ids, **kwargs):
    formation_notify(
        'noti:{0}'.format(char_id),
        char_id,
        formation = socket_ids
    )



formation_changed_signal.connect(
    _formation_changed,
    dispatch_uid = 'core.callbacks.formation._formation_changed'
)