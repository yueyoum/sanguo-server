# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

from mongoengine import DoesNotExist

from core.exception import SanguoException
from core.mongoscheme import MongoAttachment, MongoEmbededAttachment, MongoEmbededAttachmentEquipment
from core.msgpipe import publish_to_char
from utils import pack_msg

from protomsg import PrizeNotify, Attachment as MsgAttachment

from preset import errormsg


def make_standard_drop_from_template():
    return {
        'gold': 0,
        'sycee': 0,
        'exp': 0,
        'official_exp': 0,
        'heros': [],
        'equipments': [],
        'gems': [],
        'stuffs': [],
    }


def standard_drop_to_attachment_protomsg(data):
    # data is dict, {
    # 'gold': 0,
    # 'sycee': 0,
    # 'exp': 0,
    # 'official_exp': 0,
    # 'heros': [{id: amount:}, ...],
    # 'equipments': [{id: level: amount:}, ...],
    # 'gems': [{id: amount:}, ...],
    # 'stuffs': [{id: amount:}, ...]
    # }

    # TODO, modify proto
    msg = MsgAttachment()
    msg.gold = data.get('gold', 0)
    msg.sycee = data.get('sycee', 0)
    msg.exp = data.get('exp', 0)
    msg.official_exp = data.get('official_exp', 0)
    for x in data.get('heros', []):
        msg.heros.append(x['id'])
    for x in data.get('equipments', []):
        msg_e = msg.equipments.add()
        msg_e.id = x['id']
        msg_e.level = x['level']
        msg_e.step = 1
        msg_e.amount = x['amount']

    for x in data.get('gems', []):
        msg_g = msg.gems.add()
        msg_g.id = x['id']
        msg_g.amount = x['amount']

    for x in data.get('stuffs', []):
        msg_s = msg.stuffs.add()
        msg_s.id = x['id']
        msg_s.amount = x['amount']

    return msg



class Attachment(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.attachment = MongoAttachment.objects.get(id=self.char_id)
        except DoesNotExist:
            self.attachment = MongoAttachment(id=self.char_id)
            self.attachment.prize_ids = []
            self.attachment.attachments = {}
            self.attachment.save()


    def save_standard_drop(self, drop, des=''):
        from core.character import Char
        from core.hero import save_hero
        from core.item import Item

        if drop['gold'] or drop['sycee'] or drop['exp'] or drop['official_exp']:
            char = Char(self.char_id)
            char.update(gold=drop['gold'], sycee=drop['sycee'], exp=drop['exp'], official_exp=drop['official_exp'], des=des)

        if drop['heros']:
            heros = []
            for h in drop['heros']:
                heros.extend([h['id']] * h['amount'])
            save_hero(self.char_id, heros)

        item = Item(self.char_id)
        for e in drop['equipments']:
            for i in range(e['amount']):
                item.equip_add(e['id'], e['level'])

        if drop['gems']:
            gems = []
            for g in drop['gems']:
                gems.append((g['id'], g['amount']))
            item.gem_add(gems)

        if drop['stuffs']:
            stuffs = []
            for s in drop['stuffs']:
                stuffs.append((s['id'], s['amount']))
            item.stuff_add(stuffs)


    def save_to_char(self, gold=0, sycee=0, exp=0, official_exp=0, heros=None, equipments=None, gems=None, stuffs=None):
        from core.character import Char
        from core.hero import save_hero
        from core.item import Item

        if gold or sycee or exp:
            char = Char(self.char_id)
            char.update(gold=gold, sycee=sycee, exp=exp, des='Attachment')

        if heros:
            save_hero(self.char_id, heros)

        item = Item(self.char_id)
        if equipments:
            for eid, level, step in equipments:
                item.equip_add(eid, level)
        if gems:
            item.gem_add(gems)

        if stuffs:
            item.stuff_add(stuffs)


    def save_to_prize(self, prize_id):
        if prize_id not in self.attachment.prize_ids:
            self.attachment.prize_ids.append(prize_id)
            self.attachment.save()
        self.send_notify()


    def save_to_attachment(self, prize_id, gold=0, sycee=0, exp=0, official_exp=0, heros=None, equipments=None, gems=None, stuffs=None):
        embeded_attachment = MongoEmbededAttachment()
        embeded_attachment.gold = gold
        embeded_attachment.exp = exp
        embeded_attachment.sycee = sycee
        embeded_attachment.official_exp = official_exp

        if heros:
            embeded_attachment.heros.extend(heros)
        if equipments:
            for _id, level, step in equipments:
                equip = MongoEmbededAttachmentEquipment()
                equip.id = _id
                equip.level = level
                equip.step = step
                equip.amount = 1

                embeded_attachment.equipments.append(equip)
        if gems:
            for _id, amount in gems:
                embeded_attachment.gems[str(_id)] = amount
        if stuffs:
            for _id, amount in stuffs:
                embeded_attachment.stuffs[str(_id)] = amount

        self.attachment.attachments[str(prize_id)] = embeded_attachment

        if prize_id not in self.attachment.prize_ids:
            self.attachment.prize_ids.append(prize_id)
        self.attachment.save()

        self.send_notify()

    def get_attachment(self, prize_id, param=0):
        if prize_id == 1:
            # 挂机
            from core.stage import Hang
            h = Hang(self.char_id)
            att_msg = h.save_drop()
        elif prize_id == 4:
            # 成就
            from core.achievement import Achievement
            ach = Achievement(self.char_id)
            att_msg = ach.get_reward(param)
        elif prize_id == 5:
            # 任务
            from core.task import Task
            task = Task(self.char_id)
            att_msg = task.get_reward(param)
        elif prize_id == 6:
            # 官职每日登录
            from core.daily import OfficalDailyReward
            od = OfficalDailyReward(self.char_id)
            att_msg = od.get_reward()
        elif prize_id == 7:
            # 团队本
            from core.stage import TeamBattle
            tb = TeamBattle(self.char_id)
            att_msg = tb.get_reward()
        else:
            try:
                attachment = self.attachment.attachments[str(prize_id)]
            except KeyError:
                raise SanguoException(
                    errormsg.ATTACHMENT_NOT_EXIST,
                    self.char_id,
                    "Attachment Get",
                    "{0} not exist".format(prize_id)
                )

            heros = None
            if attachment.heros:
                heros = [int(i) for i in attachment.heros]
            equipments = None
            if attachment.equipments:
                equipments = [(i.id, i.level, i.step) for i in attachment.equipments]
            gems = None
            if attachment.gems:
                gems = [(int(k), v) for k, v in attachment.gems.items()]
            stuffs = None
            if attachment.stuffs:
                stuffs = [(int(k), v) for k, v in attachment.stuffs.items()]

            self.save_to_char(
                gold=attachment.gold,
                sycee=attachment.sycee,
                exp=attachment.exp,
                official_exp=attachment.official_exp,
                heros=heros,
                equipments=equipments,
                gems=gems,
                stuffs=stuffs
            )

            self.attachment.attachments.pop(str(prize_id))
            self.attachment.save()

            att_msg = attachment.to_protobuf()

        # 删除此prize_id
        if prize_id in self.attachment.prize_ids:
            self.attachment.prize_ids.remove(prize_id)
        if str(prize_id) in self.attachment.attachments:
            self.attachment.attachments.pop(str(prize_id))

        self.attachment.save()
        self.send_notify()

        return att_msg



    def send_notify(self):
        msg = PrizeNotify()
        msg.prize_ids.extend(self.attachment.prize_ids)
        publish_to_char(self.char_id, pack_msg(msg))

