# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

from mongoengine import DoesNotExist

from core.character import Char
from core.hero import save_hero
from core.item import Item

from core.mongoscheme import MongoAttachment, MongoEmbededAttachment, MongoEmbededAttachmentEquipment

from core.msgpipe import publish_to_char
from utils import pack_msg

from protomsg import PrizeNotify



class Attachment(object):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.attachment = MongoAttachment.objects.get(id=self.char_id)
        except DoesNotExist:
            self.attachment = MongoAttachment(id=self.char_id)
            self.attachment.save()

    def save_to_char(self, gold=0, sycee=0, exp=0, official_exp=0, heros=None, equipments=None, gems=None, stuffs=None):
        char = Char(self.char_id)
        char.update(gold=gold, sycee=sycee, exp=exp)

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


    def save_to_attachment(self, prize_id, gold=0, sycee=0, official_exp=0, heros=None, equipments=None, gems=None, stuffs=None):
        embeded_attachment = MongoEmbededAttachment()
        embeded_attachment.gold = gold
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
        self.attachment.save()

        msg = PrizeNotify()
        msg.ids.append(prize_id)
        publish_to_char(self.char_id, pack_msg(msg))

    def get_attachment(self, prize_id):
        pass


    def send_notify(self):
        msg = PrizeNotify()
        for k in self.attachment.attachments.keys():
            msg.ids.append(int(k))
        publish_to_char(self.char_id, pack_msg(msg))

