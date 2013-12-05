from core.mongoscheme import MongoChar, MongoSocket
from core.signals import formation_changed_signal

def save_socket(char_id, socket_id=None, hero=0, weapon=0, armor=0, jewelry=0):
    c = MongoChar.objects.only('sockets').get(id=char_id)
    if not socket_id:
        socket_id = len(c.sockets) + 1
    
    socket =  c.sockets.get(str(socket_id), MongoSocket())
    
    if hero:
        socket.hero = hero
    if weapon:
        socket.weapon = weapon
    if armor:
        socket.armor = armor
    if jewelry:
        socket.jewelry = jewelry

    c.sockets[str(socket_id)] = socket
    c.save()


def save_formation(char_id, socket_ids, send_notify=True):
    c = MongoChar.objects.only('id').get(id=char_id)
    c.formation = socket_ids
    c.save()
    
    if send_notify:
        formation_changed_signal.send(
            sender = None,
            char_id = char_id,
            socket_ids = socket_ids
        )


def get_char_formation(char_id):
    c = MongoChar.objects.only('formation').get(id=char_id)
    return c.formation


def find_socket_by_hero(char_id, hero_id):
    c = MongoChar.objects.only('sockets').get(id=char_id)
    for k, v in c.sockets.iteritems():
        if v.hero == hero_id:
            return v
    
    return None


def find_socket_by_equip(char_id, equip_id):
    c = MongoChar.objects.only('sockets').get(id=char_id)
    for k, v in c.sockets.iteritems():
        if v.weapon == equip_id or v.armor == equip_id or v.jewelry == equip_id:
            return v
    
    return None


