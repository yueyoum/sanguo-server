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

from preset.settings import (
    REWARD_DROP_PROB_MULTIPLE,
    REWARD_EXP_MULTIPLE,
    REWARD_GOLD_MULTIPLE,
    REWARD_OFFICAL_EXP_MULTIPLE,
    REWARD_SYCEE_MULTIPLE,
)


# drop 分为三个阶段
# package_drop 编辑器数据，包含prob。 这个只能用于 get_drop
# prepare_drop 从 get_drop 获取，这个用于 Resource.add 的参数
# standard_drop 从 Resource.add 获取，是其返回. 这个也是最终用于填充Attachment消息的drop
#
# 在修改了 Attachment 消息后 （Hero中也添加了 amount）
# 这里 prepare_drop 和 standard_drop 已经统一了。
# 现在它们的区分就是 prepare_drop 中的 heros [(id, amount)] amount 可能 > 1
# 但 standard_drop 中的 amount 一定为 1
# 也就是 prepare_drop 是原始数据，里面可能包含多个 一样的 hero
# 但是在save的时候 最多只有一个hero save成功，其他的全部变成 同名卡魂。
# 所以 Resource.add 返回的 standard_drop 就是处理过后的 prepare_drop
# hero amount一定为1, 并且可能会多添加一些 souls

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
    # 'heros': [(id, amount), ...],
    # 'souls': [(id, amount), ...],
    # 'equipments': [(id, level, amount), ...],
    # 'gems': [(id, amount), ...],
    # 'stuffs': [(id, amount), ...]
    # }

    msg = MsgAttachment()
    msg.gold = data.get('gold', 0)
    msg.sycee = data.get('sycee', 0)
    msg.exp = data.get('exp', 0)
    msg.official_exp = data.get('official_exp', 0)

    for _id, _amount in data.get('heros', []):
        msg_h = msg.heros.add()
        msg_h.id = _id
        msg_h.amount = _amount

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


def get_drop_from_mode_two_package(package):
    # 只生成一样东西
    # 或者什么也没有
    drop = make_standard_drop_from_template()

    def _all_items(name):
        if not package[name]:
            return []

        return [(name, p) for p in package[name]]

    names = ['heros', 'souls', 'equipments', 'gems', 'stuffs']
    items = []
    for name in names:
        items.extend(_all_items(name))

    if not items:
        return drop

    name, item = random.choice(items)
    a, b = divmod(item['prob'] * REWARD_DROP_PROB_MULTIPLE, DROP_PROB_BASE)
    a = int(a)
    if b > random.randint(0, DROP_PROB_BASE):
        a += 1

    if a < 1:
        return drop

    if name == 'equipments':
        drop[name]  = [(item['id'], item['level'], a)]
    else:
        drop[name] = [(item['id'], a)]

    return drop


def get_drop_from_raw_package(package, multi=1, gaussian=False):
    if package.get('mode', 1) == 2:
        return get_drop_from_mode_two_package(package)

    gold = package['gold']
    sycee = package['sycee']
    exp = package['exp']
    official_exp = package['official_exp']
    heros = package['heros']
    souls = package['souls']
    equipments = package['equipments']
    gems = package['gems']
    stuffs = package['stuffs']

    def _make(items):
        final_items = []
        for item in items:
            prob = item['prob'] * multi * REWARD_DROP_PROB_MULTIPLE
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
        'gold': gold * multi * REWARD_GOLD_MULTIPLE,
        'sycee': sycee * multi * REWARD_SYCEE_MULTIPLE,
        'exp': exp * multi * REWARD_EXP_MULTIPLE,
        'official_exp': official_exp * multi * REWARD_OFFICAL_EXP_MULTIPLE,
        'heros': [(x['id'], x['amount']) for x in heros],
        'souls': [(x['id'], x['amount']) for x in souls],
        'equipments': [(x['id'], x['level'], x['amount']) for x in equipments],
        'gems': [(x['id'], x['amount']) for x in gems],
        'stuffs': [(x['id'], x['amount']) for x in stuffs],
    }



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

    drop = make_standard_drop_from_template()

    for d in drop_ids:
        if d == 0:
            # 一般不会为0，0实在策划填写编辑器的时候本来为空，却填了个0
            continue

        pack = copy.deepcopy(PACKAGES[d])

        p = get_drop_from_raw_package(pack, multi=multi, gaussian=gaussian)

        drop['gold'] += p['gold']
        drop['sycee'] += p['sycee']
        drop['exp'] += p['exp']
        drop['official_exp'] += p['official_exp']

        drop['heros'].extend(p['heros'])
        drop['souls'].extend(p['souls'])
        drop['equipments'].extend(p['equipments'])
        drop['gems'].extend(p['gems'])
        drop['stuffs'].extend(p['stuffs'])

    def _merge(items):
        result = {}
        for item in items:
            result[item[0]] = result.get(item[0], 0) + item[1]

        return result.items()

    def _merge_equipment(items):
        result = []
        for item in items:
            _id, level, amount = item
            for res in result:
                if res[0] == _id and res[1] == level:
                    res[2] += amount
                    break
            else:
                result.append((_id, level, amount))
        return result

    drop['heros'] = _merge(drop['heros'])
    drop['souls'] = _merge(drop['souls'])
    drop['gems'] = _merge(drop['gems'])
    drop['stuffs'] = _merge(drop['stuffs'])
    drop['equipments'] = _merge_equipment(drop['equipments'])

    return drop


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
            if ach.has_prizes():
                prize_id = None

        elif prize_id == 5:
            # 任务
            from core.task import Task
            task = Task(self.char_id)
            att_msg = task.get_reward(param)
            if task.has_prizes():
                prize_id = None

        elif prize_id == 6:
            # 官职每日登录
            # from core.daily import OfficialDailyReward
            # od = OfficialDailyReward(self.char_id)
            # att_msg = od.get_reward()
            att_msg = None
        elif prize_id == 7:
            # 团队本
            att_msg = None

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
        if prize_id:
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

