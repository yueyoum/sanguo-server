# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '2/19/14'

import random
import copy
import json

from mongoengine import DoesNotExist

from core.resource import Resource
from core.exception import SanguoException
from core.mongoscheme import MongoAttachment
from core.msgpipe import publish_to_char
from utils.math import GAUSSIAN_TABLE
from utils import pack_msg

from protomsg import PrizeNotify, Attachment as MsgAttachment

from preset import errormsg
from preset.data import PACKAGES
from preset.settings import DROP_PROB_BASE


# drop 分为三个阶段，三种状态
# package_drop 编辑器数据，包含prob。 这个只能用于 get_drop
# prepare_drop 从 get_drop 获取，这个用于 Resource.add
# standard_drop 从 Resource.add 获取，这个也是最终用于填充Attachment消息的drop
# standard_drop 与 prepare_drop 的唯一区别在于，prepare_drop 中的 heros 格式为 [(id, amount)...]. 但standard_drop为 [id,id...]

def make_standard_drop_from_template():
    return {
        'gold': 0,
        'sycee': 0,
        'exp': 0,
        'official_exp': 0,
        'heros': [],
        'souls': [],
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
    # 'heros': [id, id...],
    # 'souls': [(id, amount), ...]
    # 'equipments': [(id, level, amount), ...],
    # 'gems': [(id, amount), ...],
    # 'stuffs': [(id, amount), ...]
    # }

    msg = MsgAttachment()
    msg.gold = data.get('gold', 0)
    msg.sycee = data.get('sycee', 0)
    msg.exp = data.get('exp', 0)
    msg.official_exp = data.get('official_exp', 0)

    for x in data.get('heros', []):
        msg_h = msg.heros.add()
        msg_h.id = x

    for _id, _amount in data.get('souls', []):
        msg_soul = msg.souls.add()
        msg_soul.id = _id
        msg_soul.amount = _amount

    for _id, _level, _amount in data.get('equipments', []):
        msg_e = msg.equipments.add()
        msg_e.id = _id
        msg_e.level = _level
        msg_e.amount = _amount

    for _id, _amount in data.get('gems', []):
        msg_g = msg.gems.add()
        msg_g.id = _id
        msg_g.amount = _amount

    for _id, _amount in data.get('stuffs', []):
        msg_s = msg.stuffs.add()
        msg_s.id = _id
        msg_s.amount = _amount

    return msg


def get_drop(drop_ids, multi=1, gaussian=False):
    # 从pakcage中解析并计算掉落，返回为 dict
    # package 格式
    # {
    #     'gold': 0,
    #     'sycee': 0,
    #     'exp': 0,
    #     'official_exp': 0,
    #     'heros': [
    #         {id: amount: prob:},...
    #     ],
    #     'souls': [
    #         {id: amount: prob:},...
    #     ],
    #     'equipments': [
    #         {id: level: amount: prob:},...
    #     ],
    #     'gems': [
    #         {id: amount: prob:},...
    #     ],
    #     'stuffs': [
    #         {id: amount: prob:},...
    #     ]
    # }
    #
    # 返回的是从prob概率计算后的 prepare_drop 格式
    # {
    #     'gold': 0,
    #     'sycee': 0,
    #     'exp': 0,
    #     'official_exp': 0,
    #     'heros': [(id, amount)...],
    #     'souls': [(id, amount)...],
    #     'equipments': [(id, level, amount)...],
    #     'gems': [(id, amount)...],
    #     'stuffs': [(id, amount)...]
    # }

    gold = 0
    sycee = 0
    exp = 0
    official_exp = 0
    heros = []
    souls = []
    equipments = []
    gems = []
    stuffs = []

    for d in drop_ids:
        if d == 0:
            # 一般不会为0，0实在策划填写编辑器的时候本来为空，却填了个0
            continue

        p = copy.deepcopy(PACKAGES[d])
        gold += p['gold']
        sycee += p['sycee']
        exp += p['exp']
        official_exp += p['official_exp']

        heros.extend(p['heros'])
        souls.extend(p['souls'])
        equipments.extend(p['equipments'])
        gems.extend(p['gems'])
        stuffs.extend(p['stuffs'])

    def _make(items):
        final_items = []
        for item in items:
            prob = item['prob'] * multi
            if gaussian:
                prob = prob * (1 + GAUSSIAN_TABLE[round(random.uniform(0.01, 0.99), 2)] * 0.08)

            a, b = divmod(prob, DROP_PROB_BASE)
            a = int(a)
            if b > random.randint(0, DROP_PROB_BASE):
                a += 1

            if a == 0:
                continue

            item['amount'] *= a
            final_items.append(item)

        return final_items

    heros = _make(heros)
    souls = _make(souls)
    equipments = _make(equipments)
    gems = _make(gems)
    stuffs = _make(stuffs)

    return {
        'gold': gold * multi,
        'sycee': sycee * multi,
        'exp': exp * multi,
        'official_exp': official_exp * multi,
        'heros': [(x['id'], x['amount']) for x in heros],
        'souls': [(x['id'], x['amount']) for x in souls],
        'equipments': [(x['id'], x['level'], x['amount']) for x in equipments],
        'gems': [(x['id'], x['amount']) for x in gems],
        'stuffs': [(x['id'], x['amount']) for x in stuffs],
    }


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

    def save_to_prize(self, prize_id):
        if prize_id not in self.attachment.prize_ids:
            self.attachment.prize_ids.append(prize_id)
            self.attachment.save()
        self.send_notify()


    def save_to_attachment(self, prize_id, **kwargs):
        self.attachment.attachments[str(prize_id)] = json.dumps(kwargs)

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

            attachment = json.loads(attachment)
            resource = Resource(self.char_id, "Prize {0}".format(prize_id))
            standard_drop = resource.add(**attachment)

            self.attachment.attachments.pop(str(prize_id))
            self.attachment.save()

            att_msg = standard_drop_to_attachment_protomsg(standard_drop)

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

