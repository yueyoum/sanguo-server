from core.signals import char_changed_signal

from core.notify import character_notify

def _char_changed(char_id, **kwargs):
    character_notify(char_id)


char_changed_signal.connect(
    _char_changed,
    dispatch_uid = 'core.callbacks.character._char_changed'
)
