from core.signals import char_updated_signal
from core.notify import hero_notify
from core.character import Char
from utils import cache



def _char_updated(char_id, **kwargs):
    char = Char(char_id)
    heros_dict = char.heros_dict

    for hid in heros_dict.keys():
        cache.delete('hero:{0}'.format(hid))

    heros = char.heros
    hero_notify(char_id, heros)

char_updated_signal.connect(
    _char_updated,
    dispatch_uid='callbacks.signals.character._char_updated'
)

