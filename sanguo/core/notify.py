import base64

from drives import redis_client
from utils import pack_msg
from core import DEFAULT
import protomsg

def character_notify(key, obj):
    data = protomsg.CharacterNotify()
    data.char.id = obj.id
    data.char.name = obj.name
    data.char.gold = obj.gold
    data.char.gem = obj.gem
    data.char.level = obj.level
    data.char.current_honor = obj.honor
    # FIXME
    data.char.max_honor = 1000
    redis_client.rpush(key, pack_msg(data))

def hero_notify(key, objs, message_name="HeroNotify"):
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

    redis_client.rpush(key, pack_msg(data))

def add_hero_notify(key, objs):
    hero_notify(key, objs, "AddHeroNotify")

def remove_hero_notify(key, ids):
    data = protomsg.RemoveHeroNotify()
    data.ids.extend(ids)
    redis_client.rpush(key, pack_msg(data))


def update_hero_notify(key, objs):
    hero_notify(key, objs, "UpdateHeroNotify")


def get_hero_panel_notify(key, char_obj):
    msg = protomsg.GetHeroPanelNotify()
    # FIXME
    data = [
            (1, 100, 0, 0),
            (2, 100, 5, 10),
            (3, 100, 10, 10),
            ]

    for d in data:
        m = msg.get_heros.add()
        m.mode, m.cost, m.free_times, m.max_free_times = d

    redis_client.rpush(key, pack_msg(msg))


def formation_notify(key, char_obj=None, formation=None):
    msg = protomsg.FormationNotify()
    if not formation:
        formation = char_obj.formation
        if not formation:
            formation = DEFAULT.FORMATION

    msg.formation.MergeFromString(base64.b64decode(formation))
    redis_client.rpush(key, pack_msg(msg))


def login_notify(key, char_obj, hero_objs=None):
    if not hero_objs:
        hero_objs = char_obj.char_heros.all()

    character_notify(key, char_obj)
    hero_notify(key, hero_objs)
    get_hero_panel_notify(key, char_obj)
    formation_notify(key, char_obj=char_obj)

