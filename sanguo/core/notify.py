from core.rabbit import publish_to_char
from utils import pack_msg
from core.character import (
    get_char_formation,
    get_char_hero_objs,
    get_char_equipment_objs,
    )

from core.stage import get_already_stage, get_new_stage
from core import GLOBAL
from core.mongoscheme import MongoChar, Hang, DoesNotExist, Prison
import protomsg

from apps.character.cache import get_cache_character
from core.hero import cal_hero_property

def character_notify(obj):
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
    # FIXME
    data.char.power = 100
    publish_to_char(obj.id, pack_msg(data))

def hero_notify(char_id, objs, message_name="HeroNotify"):
    Msg = getattr(protomsg, message_name)
    data = Msg()

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

    publish_to_char(char_id, pack_msg(data))

def add_hero_notify(char_id, objs):
    hero_notify(char_id, objs, "AddHeroNotify")

def remove_hero_notify(char_id, ids):
    data = protomsg.RemoveHeroNotify()
    data.ids.extend(ids)
    publish_to_char(char_id, pack_msg(data))


def update_hero_notify(char_id, objs):
    hero_notify(char_id, objs, "UpdateHeroNotify")


def get_hero_panel_notify(char_obj):
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

    publish_to_char(char_obj.id, pack_msg(msg))

def socket_notify(char_id):
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

    publish_to_char(char_id, pack_msg(msg))



def formation_notify(char_id, formation=None):
    msg = protomsg.FormationNotify()
    if not formation:
        formation = get_char_formation(char_id)

    msg.socket_ids.extend(formation)
    publish_to_char(char_id, pack_msg(msg))


def already_stage_notify(char_id):
    data = get_already_stage(char_id)
    if data:
        msg = protomsg.AlreadyStageNotify()
        for d in data.items():
            stage = msg.stages.add()
            stage.id, stage.star = d

        publish_to_char(char_id, pack_msg(msg))


def current_stage_notify(char_id, sid, star):
    msg = protomsg.CurrentStageNotify()
    msg.stage.id, msg.stage.star = sid, star
    publish_to_char(char_id, pack_msg(msg))

def new_stage_notify(char_id, sid):
    msg = protomsg.NewStageNotify()
    msg.stage.id, msg.stage.star = sid, False
    publish_to_char(char_id, pack_msg(msg))



def equipment_notify(char_id, objs=None, message="EquipNotify"):
    if not objs:
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
    
    publish_to_char(char_id, pack_msg(msg))


def add_equipment_notify(char_id, obj):
    if isinstance(obj, (list, tuple)):
        objs = obj
    else:
        objs = [obj]
    equipment_notify(char_id, objs=objs, message="AddEquipNotify")
    
def update_equipment_notify(char_id, obj):
    if isinstance(obj, (list, tuple)):
        objs = obj
    else:
        objs = [obj]
    equipment_notify(char_id, objs=objs, message="UpdateEquipNotify")

def remove_equipment_notify(char_id, _id):
    if isinstance(_id, (list, tuple)):
        ids = _id
    else:
        ids = [_id]
    
    msg = protomsg.RemoveEquipNotify()
    msg.ids.extend(ids)
    
    publish_to_char(char_id, pack_msg(msg))


def gem_notify(char_id, gems=None, message="GemNotify"):
    if gems is None:
        mongo_char = MongoChar.objects.only('gems').get(id=char_id)
        gems = [(int(k), v) for k, v in mongo_char.gems.iteritems()]
    
    msg = getattr(protomsg, message)()
    for k, v in gems:
        g = msg.gems.add()
        g.id, g.amount = k, v
    
    publish_to_char(char_id, pack_msg(msg))


def add_gem_notify(char_id, gems):
    gem_notify(char_id, gems=gems, message="AddGemNotify")

def update_gem_notify(char_id, gems):
    gem_notify(char_id, gems=gems, message="UpdateGemNotify")

def remove_gem_notify(char_id, _id):
    if isinstance(_id, (list, tuple)):
        ids = _id
    else:
        ids = [_id]
    
    msg = protomsg.RemoveGemNotify()
    msg.ids.extend(ids)
    
    publish_to_char(char_id, pack_msg(msg))



def hang_notify(char_id):
    char = MongoChar.objects.only('hang_hours').get(id=char_id)
    try:
        hang = Hang.objects.get(id=char_id)
    except DoesNotExist:
        hang = None
    
    hang_notify_with_data(char_id, char.hang_hours, hang)
    return hang

def hang_notify_with_data(char_id, hours, hang):
    msg = protomsg.HangNotify()
    # FIXME
    msg.hours = hours or 8
    if hang is not None:
        msg.hang.stage_id = hang.stage_id
        msg.hang.whole_hours = hang.hours
        msg.hang.start_time = hang.start
        # FIXME
        msg.hang.finished = hang.finished
    
    publish_to_char(char_id, pack_msg(msg))

    

def prize_notify(char_id, prize_id):
    if isinstance(prize_id, (list, tuple)):
        ids = prize_id
    else:
        ids = [prize_id]
    
    msg = protomsg.PrizeNotify()
    msg.prize_ids.extend(ids)
    publish_to_char(char_id, pack_msg(msg))
    
def plunder_notify(char_id, amount):
    msg = protomsg.PlunderNotify()
    msg.amount = amount
    publish_to_char(char_id, pack_msg(msg))


def prisoner_notify(char_id, objs=None, message_name="PrisonerListNotify"):
    if not objs:
        prison = Prison.objects.get(id=char_id)
        objs = prison.prisoners.values()
    
    cache_char = get_cache_character(char_id)
    level = cache_char.level
    
    msg = getattr(protomsg, message_name)()
    for o in objs:
        p = msg.prisoner.add()
        p.id = o.id
        p.oid = o.oid
        p.start_time = o.start_time
        p.status = o.status
        
        # FIXME
        p.value = 5
        
        p.attack, p.defense, p.hp = cal_hero_property(o.oid, level)
        p.crit, p.dodge = 0, 0
    
    publish_to_char(char_id, pack_msg(msg))
    
def update_prisoner_notify(char_id, mongo_prisoner_obj):
    prisoner_notify(char_id, objs=[mongo_prisoner_obj], message_name="UpdatePrisonerNotify")

def new_prisoner_notify(char_id, mongo_prisoner_obj):
    prisoner_notify(char_id, objs=[mongo_prisoner_obj], message_name="NewPrisonerNotify")

def remove_prisoner_notify(char_id, _id):
    if isinstance(_id, (list, tuple)):
        ids = _id
    else:
        ids = [_id]
    
    msg = protomsg.RemovePrisonerNotify()
    msg.ids.extend(ids)
    publish_to_char(char_id, pack_msg(msg))



def prison_notify(char_id, slots):
    msg = protomsg.PrisonNotify()
    msg.slots = slots
    publish_to_char(char_id, pack_msg(msg))


def arena_notify(char_id):
    # FIXME
    msg = protomsg.ArenaNotify()
    msg.week_rank = 1
    msg.week_score = 2
    msg.day_rank = 3
    msg.day_score = 4
    msg.remained_amount = 5
    
    nb = [
        (1, 1, 'aaa'),
        (2, 2, 'bbb'),
        (3, 3, 'ccc'),
    ]
    for x in nb:
        n = msg.chars.add()
        n.rank, n.id, n.name = x
    
    publish_to_char(char_id, pack_msg(msg))


def login_notify(char_obj):
    hero_objs = get_char_hero_objs(char_obj.id)

    character_notify(char_obj)
    hero_notify(char_obj.id, hero_objs)
    get_hero_panel_notify(char_obj)
    socket_notify(char_obj.id)
    formation_notify(char_obj.id)
    already_stage_notify(char_obj.id)

    new_stages = get_new_stage(char_obj.id)
    if new_stages:
        new_stage_notify(char_obj.id, new_stages)
    
    equipment_notify(char_obj.id)
    gem_notify(char_obj.id)

    hang = hang_notify(char_obj.id)
    if hang and hang.finished:
        prize_notify(char_obj.id, 1)
    
    # FIXME
    plunder_notify(char_obj.id, 10)
    prisoner_notify(char_obj.id)
    # FIXME
    prison_notify(char_obj.id, 3)
    
    arena_notify(char_obj.id)
    

