from core.signals import char_changed_signal

from core.notify import character_notify

def _char_changed(char_obj, **kwargs):
    character_notify(char_obj)


char_changed_signal.connect(
    _char_changed,
    dispatch_uid = 'core.callbacks.character._char_changed'
)
