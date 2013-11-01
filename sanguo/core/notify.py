from drives import redis_client
from utils import pack_msg
from core.hero import Hero
from core.functional import decode_formation
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

    objs = [Hero(o) for o in objs]

    for obj in objs:
        g = data.heros.add()
        g.id = obj.id
        g.original_id = obj.original_id
        g.level = obj.level
        g.exp = obj.current_exp
        g.next_level_exp = obj.next_level_exp

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


def formation_notify(key, char_obj=None, formation=None):
    msg = protomsg.FormationNotify()
    if not formation:
        formation = char_obj.formation

    msg.formation.MergeFrom(decode_formation(formation))
    redis_client.rpush(key, pack_msg(msg))


def already_stage_notify(key, char_id):
    data = [(2, True)]
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


def login_notify(key, char_obj, hero_objs=None):
    if not hero_objs:
        hero_objs = char_obj.char_heros.all()

    character_notify(key, char_obj)
    hero_notify(key, hero_objs)
    get_hero_panel_notify(key, char_obj)
    formation_notify(key, char_obj=char_obj)
    already_stage_notify(key, char_obj.id)
    new_stage_notify(key, 3)


