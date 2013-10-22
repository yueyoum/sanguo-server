from core import redis_client
from utils import pack_msg
import msg

def character_notify(key, obj, session):
    data = msg.CharacterNotify()
    data.char.id = obj.id
    data.char.name = obj.name
    data.char.gold = obj.gold
    data.char.gem = obj.gem
    data.char.level = obj.level
    data.char.exp = obj.exp
    redis_client.rpush(key, pack_msg(data, session))

def general_notify(key, objs, session):
    data = msg.GeneralNotify()

    for obj in objs:
        g = data.general.add()
        g.id = obj.id
        g.original_id = obj.original_id
        g.level = obj.level
        g.exp = obj.exp

        # FIXME
        g.attack = 100
        g.defense = 100
        g.hp = 100

        g.attack_grow = 100
        g.defense_grow = 100
        g.hp_grow = 100

        g.cirt = 100
        g.dodge = 100

    redis_client.rpush(key, pack_msg(data, session))

def login_notify(key, char_obj, general_objs):
    character_notify(key, char_obj)
    general_notify(key, general_objs)

