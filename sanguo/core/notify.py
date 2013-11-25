from core.drives import redis_client, document_char
from utils import pack_msg
from core.hero import Hero
from core.character import get_char_formation
from core.stage import get_already_stage, get_new_stage
from core import GLOBAL
import protomsg

def character_notify(key, obj):
    data = protomsg.CharacterNotify()
    data.char.id = obj.id
    data.char.name = obj.name
    data.char.gold = obj.gold
    data.char.gem = obj.gem
    data.char.level = obj.level
    
    _ ,current_exp, next_level_exp = GLOBAL.LEVEL_TOTALEXP[obj.exp]
    data.char.current_exp = current_exp
    data.char.next_level_exp = next_level_exp
    
    data.char.official = obj.official
    redis_client.rpush(key, pack_msg(data))

def hero_notify(key, objs, message_name="HeroNotify"):
    Msg = getattr(protomsg, message_name)
    data = Msg()

    objs = [Hero(o.id, o.hero_id, o.exp, []) for o in objs]

    for obj in objs:
        g = data.heros.add()
        g.id = obj.id
        g.original_id = obj.original_id

        # FIXME
        g.attack = obj.attack
        g.defense = obj.defense
        g.hp = obj.hp

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

def socket_notify(key, char_id):
    msg = protomsg.SocketNotify()
    data = document_char.get(char_id, socket=1, _id=0)
    if not data:
        return

    sockets = data.get('socket', {})
    for k, v in sockets.iteritems():
        s = msg.sockets.add()
        s.id = int(k)
        s.hero_id = v.get('hero', 0)
        s.weapon_id = v.get('weapon', 0)
        s.armor_id = v.get('armor', 0)
        s.jewelry_id = v.get('jewelry', 0)

    redis_client.rpush(key, pack_msg(msg))



def formation_notify(key, char_id, formation=None):
    msg = protomsg.FormationNotify()
    if not formation:
        formation = get_char_formation(char_id)

    msg.socket_ids.extend(formation)
    redis_client.rpush(key, pack_msg(msg))


def already_stage_notify(key, char_id):
    data = get_already_stage(char_id)
    if data:
        msg = protomsg.AlreadyStageNotify()
        for d in data:
            stage = msg.stages.add()
            stage.id, stage.star = d

        redis_client.rpush(key, pack_msg(msg))


def current_stage_notify(key, sid, star):
    msg = protomsg.CurrentStageNotify()
    msg.stage.id, msg.stage.star = sid, star
    redis_client.rpush(key, pack_msg(msg))

def new_stage_notify(key, sid):
    msg = protomsg.NewStageNotify()
    msg.stage.id, msg.stage.star = sid, False
    redis_client.rpush(key, pack_msg(msg))


def login_notify(key, char_obj):
    hero_objs = char_obj.char_heros.all()

    character_notify(key, char_obj)
    hero_notify(key, hero_objs)
    get_hero_panel_notify(key, char_obj)
    socket_notify(key, char_obj.id)
    formation_notify(key, char_id=char_obj.id)
    already_stage_notify(key, char_obj.id)

    new_stages = get_new_stage(char_obj.id)
    if new_stages:
        new_stage_notify(key, new_stages)


