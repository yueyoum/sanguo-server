from base64 import b64decode, b64encode
from core.drives import document_char

import protomsg

def save_socket(char_id, socket_id=None, hero=None, weapon=None, armor=None, jewelry=None):
    if not socket_id:
        data = document_char.get(char_id, socket=1)
        socket = data.get('socket', {})
        socket_id = len(socket) + 1


    data = {}
    if hero:
        data['socket.%d.hero' % socket_id] = hero
    if weapon:
        data['socket.%d.weapon' % socket_id] = weapon
    if armor:
        data['socket.%d.armor' % socket_id] = armor
    if jewelry:
        data['socket.%d.jewelry' % socket_id] = jewelry

    document_char.set(char_id, **data)


def save_formation(char_id, socket_ids):
    document_char.set(char_id, formation=socket_ids)


def get_char_formation(char_id):
    data = document_char.get(char_id, formation=1)
    return data['formation']

