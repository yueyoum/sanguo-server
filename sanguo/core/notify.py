from core.drives import redis_client
from utils import pack_msg
from core.character import (
    get_char_formation,
    get_char_hero_objs,
    get_char_equipment_objs,
    )

from core.stage import get_already_stage, get_new_stage
from core import GLOBAL
from core.mongoscheme import MongoChar, Hang, DoesNotExist
import protomsg

def character_notify(key, obj):
    data = protomsg.CharacterNotify()
    data.char.id = obj.id
    data.char.name = obj.name
    data.char.gold = obj.gold
    data.char.gem = obj.sycee
    data.char.level = obj.level
    
    _ ,current_exp, next_level_exp = GLOBAL.LEVEL_TOTALEXP[obj.exp]
    data.char.current_exp = current_exp
    data.char.next_level_exp = next_level_exp
    
    data.char.official = obj.official
    redis_client.rpush(key, pack_msg(data))

def hero_notify(key, objs, message_name="HeroNotify"):
    Msg = getattr(protomsg, message_name)
    data = Msg()

    #objs = [Hero(o.id, o.original_id, o.level, []) for o in objs]

    for obj in objs:
        g = data.heros.add()
        g.id = int(obj.id)
        g.original_id = obj.oid

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
    data = MongoChar.objects.only('sockets').get(id=char_id)
    if not data:
        return

    sockets = data.sockets
    for k, v in sockets.iteritems():
        s = msg.sockets.add()
        s.id = int(k)
        s.hero_id = v.hero or 0
        s.weapon_id = v.weapon or 0
        s.armor_id = v.armor or 0
        s.jewelry_id = v.jewelry or 0

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
        for d in data.items():
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



def equipment_notify(key, char_id=None, objs=None, message="EquipNotify"):
    if not objs:
        if not char_id:
            raise Exception("equipment_notify: bad arguments")
        
        objs = get_char_equipment_objs(char_id)

    msg = getattr(protomsg, message)()
    for obj in objs:
        e = msg.equips.add()
        e.id = int(obj.id)
        e.oid = obj.tid
        e.name = obj.name
        e.level = obj.level
        e.exp = obj.exp
        e.value = obj.value
        
        e.whole_hole = obj.hole_amount
        e.gem_ids.extend(obj.gems)
        
        for attr in obj.decoded_random_attrs:
            k, v = attr.items()[0]
            a = e.attrs.add()
            a.id = k
            a.value = v['value']
    
    redis_client.rpush(key, pack_msg(msg))


def add_equipment_notify(key, obj):
    if isinstance(obj, (list, tuple)):
        objs = obj
    else:
        objs = [obj]
    equipment_notify(key, objs=objs, message="AddEquipNotify")
    
def update_equipment_notify(key, obj):
    if isinstance(obj, (list, tuple)):
        objs = obj
    else:
        objs = [obj]
    equipment_notify(key, objs=objs, message="UpdateEquipNotify")

def remove_equipment_notify(key, _id):
    if isinstance(_id, (list, tuple)):
        ids = _id
    else:
        ids = [_id]
    
    msg = protomsg.RemoveEquipNotify()
    msg.ids.extend(ids)
    
    redis_client.rpush(key, pack_msg(msg))


def gem_notify(key, char_id=None, gems=None, message="GemNotify"):
    if gems is None:
        if char_id is None:
            raise Exception("gem_notify: bad arguments")
        
        mongo_char = MongoChar.objects.only('gems').get(id=char_id)
        gems = [(int(k), v) for k, v in mongo_char.gems.iteritems()]
    
    msg = getattr(protomsg, message)()
    for k, v in gems:
        g = msg.gems.add()
        g.id, g.amount = k, v
    
    redis_client.rpush(key, pack_msg(msg))


def add_gem_notify(key, gems):
    gem_notify(key, gems=gems, message="AddGemNotify")

def update_gem_notify(key, gems):
    gem_notify(key, gems=gems, message="UpdateGemNotify")

def remove_gem_notify(key, _id):
    if isinstance(_id, (list, tuple)):
        ids = _id
    else:
        ids = [_id]
    
    msg = protomsg.RemoveGemNotify()
    msg.ids.extend(ids)
    
    redis_client.rpush(key, pack_msg(msg))



def hang_notify(key, char_id):
    char = MongoChar.objects.only('hang_hours').get(id=char_id)
    try:
        hang = Hang.objects.get(id=char_id)
    except DoesNotExist:
        hang = None
    
    hang_notify_with_data(key, char.hang_hours, hang)
    return hang

def hang_notify_with_data(key, hours, hang):
    msg = protomsg.HangNotify()
    # FIXME
    msg.hours = hours or 8
    if hang is not None:
        msg.hang.stage_id = hang.stage_id
        msg.hang.whole_hours = hang.hours
        msg.hang.start_time = hang.start
        # FIXME
        msg.hang.finished = hang.finished
    
    redis_client.rpush(key, pack_msg(msg))

    

def prize_notify(key, prize_id):
    if isinstance(prize_id, (list, tuple)):
        ids = prize_id
    else:
        ids = [prize_id]
    
    msg = protomsg.PrizeNotify()
    msg.prize_ids.extend(ids)
    redis_client.rpush(key, pack_msg(msg))
    


def login_notify(key, char_obj):
    hero_objs = get_char_hero_objs(char_obj.id)

    character_notify(key, char_obj)
    hero_notify(key, hero_objs)
    get_hero_panel_notify(key, char_obj)
    socket_notify(key, char_obj.id)
    formation_notify(key, char_id=char_obj.id)
    already_stage_notify(key, char_obj.id)

    new_stages = get_new_stage(char_obj.id)
    if new_stages:
        new_stage_notify(key, new_stages)
    
    equipment_notify(key, char_id=char_obj.id)
    gem_notify(key, char_id=char_obj.id)

    hang = hang_notify(key, char_obj.id)
    if hang and hang.finished:
        prize_notify(key, 1)

