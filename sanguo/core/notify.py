from utils import pack_msg
from core.mongoscheme import MongoPrison
import protomsg

from core.character import Char
from core.task import Task

from core.hero import cal_hero_property

from core.msgpipe import publish_to_char
from preset.settings import PLUNDER_COST_SYCEE
from core.counter import Counter
from core.prison import Prison
from core.friend import Friend
from core.mail import Mail
from core.daily import CheckIn

from core.stage import Stage, Hang

from core.formation import Formation
from core.item import Item
from core.heropanel import HeroPanel

from apps.character.models import Character


def hero_notify(char_id, objs, message_name="HeroNotify"):
    data = getattr(protomsg, message_name)()

    for obj in objs:
        g = data.heros.add()
        g.id = obj.id
        g.original_id = obj.oid

        g.attack = int(obj.attack)
        g.defense = int(obj.defense)
        g.hp = int(obj.hp)
        g.cirt = int(obj.crit)

        g.step = obj.step
        # FIXME
        g.step_cost = 1

    publish_to_char(char_id, pack_msg(data))


def add_hero_notify(char_id, objs):
    hero_notify(char_id, objs, "AddHeroNotify")


def remove_hero_notify(char_id, ids):
    data = protomsg.RemoveHeroNotify()
    data.ids.extend(ids)
    publish_to_char(char_id, pack_msg(data))


def update_hero_notify(char_id, objs):
    hero_notify(char_id, objs, "UpdateHeroNotify")


def hang_notify_with_data(char_id, hours, max_hours, hang):
    msg = protomsg.HangNotify()
    # FIXME
    msg.hours = hours or 8
    msg.max_hours = max_hours
    if hang is not None:
        msg.hang.stage_id = hang.stage_id
        msg.hang.whole_hours = hang.hours
        msg.hang.start_time = hang.start
        # FIXME
        msg.hang.finished = hang.finished

    publish_to_char(char_id, pack_msg(msg))


def plunder_notify(char_id):
    count = Counter(char_id, 'plunder')
    msg = protomsg.PlunderNotify()
    msg.amount = count.cur_value
    msg.max_amount = count.max_value
    msg.cost_sycee = PLUNDER_COST_SYCEE
    publish_to_char(char_id, pack_msg(msg))


def prisoner_notify(char_id, objs=None, message_name="PrisonerListNotify"):
    if not objs:
        prison = MongoPrison.objects.get(id=char_id)
        objs = prison.prisoners.values()

    cache_char = Character.cache_obj(char_id)
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

        # FIXME
        p.attack, p.defense, p.hp = cal_hero_property(o.oid, level, 1)
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


def prison_notify(char_id, prison=None):
    if not prison:
        prison = Prison(char_id)
    msg = protomsg.PrisonNotify()
    msg.slots = prison.slots
    msg.max_slots = prison.max_slots
    msg.max_prisoners_amount = prison.max_prisoner_amount
    msg.open_slot_cost = prison.open_slot_cost
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


def login_notify(char_id):
    c = Char(char_id)
    hero_objs = c.heros

    c.send_notify()

    hero_notify(char_id, hero_objs)

    f = Formation(char_id)
    f.send_socket_notify()
    f.send_formation_notify()

    hang = Hang(char_id)
    hang.send_notify()


    plunder_notify(char_id)
    prisoner_notify(char_id)
    prison_notify(char_id)

    arena_notify(char_id)

    f = Friend(char_id)
    f.send_friends_notify()
    f.send_friends_amount_notify()

    m = Mail(char_id)
    m.send_mail_notify()

    CheckIn(char_id).send_notify()
    Item(char_id).send_notify()

    stage = Stage(char_id)
    stage.send_already_stage_notify()
    stage.send_new_stage_notify()

    HeroPanel(char_id).send_notify()
    Task(char_id).send_notify()
    

