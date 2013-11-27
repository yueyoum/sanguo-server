from core.mongoscheme import MongoChar, MongoSocket

def save_socket(char_id, socket_id=None, hero=0, weapon=0, armor=0, jewelry=0):
    c = MongoChar.objects.only('sockets').get(id=char_id)
    if not socket_id:
        socket_id = len(c.socket) + 1
    
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


def save_formation(char_id, socket_ids):
    c = MongoChar.objects.only('id').get(id=char_id)
    c.formation = socket_ids
    c.save()


def get_char_formation(char_id):
    c = MongoChar.objects.only('formation').get(id=char_id)
    return c.formation

