from core.signals import char_changed_signal

from core.notify import character_notify

def _char_changed(char_obj, **kwargs):
    character_notify('noti:{0}'.format(char_obj.id), char_obj)


char_changed_signal.connect(
    _char_changed,
    dispatch_uid = 'core.callbacks.character._char_changed'
)
