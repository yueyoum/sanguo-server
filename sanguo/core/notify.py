from core import redis_client
from utils import pack_msg
import protomsg

def character_notify(key, obj, session):
    data = protomsg.CharacterNotify()
    data.char.id = obj.id
    data.char.name = obj.name
    data.char.gold = obj.gold
    data.char.gem = obj.gem
    data.char.level = obj.level
    data.char.current_honor = obj.honor
    # FIXME
    data.char.max_honor = 1000
    redis_client.rpush(key, pack_msg(data, session))

def hero_notify(key, objs, session, message_name="HeroNotify"):
    Msg = getattr(protomsg, message_name)
    data = Msg()

    for obj in objs:
        g = data.heros.add()
        g.id = obj.id
        g.original_id = obj.hero_id
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

