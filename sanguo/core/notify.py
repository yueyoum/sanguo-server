from utils import pack_msg
import protomsg

from core.character import Char
from core.task import Task

from core.msgpipe import publish_to_char
from core.prison import Prison
from core.plunder import Plunder
from core.friend import Friend
from core.mail import Mail
from core.daily import CheckIn

from core.stage import Stage, Hang

from core.formation import Formation
from core.item import Item
from core.heropanel import HeroPanel


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

    Plunder(char_id).send_notify()

    p = Prison(char_id)
    p.send_prisoners_notify()
    p.send_notify()

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

