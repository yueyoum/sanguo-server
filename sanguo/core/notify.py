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

from core.stage import Stage, Hang, EliteStage, TeamBattle

from core.formation import Formation
from core.item import Item
from core.heropanel import HeroPanel
from core.arena import Arena
from core.achievement import Achievement
from core.store import Store
from core.hero import HeroSoul, char_heros_obj
from core.functionopen import FunctionOpen
from core.levy import Levy


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
        g.power = obj.power
        # FIXME
        g.max_socket_amount = obj.max_socket_amount
        g.current_socket_amount = obj.current_socket_amount

    publish_to_char(char_id, pack_msg(data))


def add_hero_notify(char_id, objs):
    hero_notify(char_id, objs, "AddHeroNotify")


def remove_hero_notify(char_id, ids):
    data = protomsg.RemoveHeroNotify()
    data.ids.extend(ids)
    publish_to_char(char_id, pack_msg(data))


def update_hero_notify(char_id, objs):
    hero_notify(char_id, objs, "UpdateHeroNotify")


def login_notify(char_id):
    hero_objs = char_heros_obj(char_id)

    Char(char_id).send_notify()

    hero_notify(char_id, hero_objs)
    Item(char_id).send_notify()

    f = Formation(char_id)
    f.send_socket_notify()
    f.send_formation_notify()

    hang = Hang(char_id)
    hang.send_notify()

    Plunder(char_id).send_notify()

    p = Prison(char_id)
    p.send_prisoners_notify()

    Arena(char_id).send_notify()

    f = Friend(char_id)
    f.send_friends_notify()
    f.send_friends_amount_notify()

    m = Mail(char_id)
    m.send_mail_notify()

    CheckIn(char_id).send_notify()


    stage = Stage(char_id)
    stage.send_already_stage_notify()
    stage.send_new_stage_notify()

    HeroPanel(char_id).send_notify()
    Task(char_id).send_notify()
    Achievement(char_id).send_notify()
    EliteStage(char_id).send_notify()
    Store(char_id).send_notify()
    TeamBattle(char_id).send_notify()
    HeroSoul(char_id).send_notify()
    FunctionOpen(char_id).send_notify()
    Levy(char_id).send_notify()


