# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-9-11'

import arrow
from mongoengine import DoesNotExist

from django.conf import settings

from core.mongoscheme import MongoAffairs, MongoEmbeddedHangLog
from core.exception import SanguoException
from core.attachment import get_drop, make_standard_drop_from_template, standard_drop_to_attachment_protomsg
from core.resource import Resource
from core.character import Char

from core.msgpipe import publish_to_char

from utils import pack_msg

from preset import errormsg
from preset.data import BATTLES, VIP_DEFINE
from preset.settings import PLUNDER_LOG_TEMPLATE, HANG_REWARD_ADDITIONAL

from protomsg import City as CityMsg, CityNotify, HangNotify

CITY_IDS = BATTLES.keys()
CITY_IDS.sort()
FIRST_CITY_ID = CITY_IDS[0]

TIME_ZONE = settings.TIME_ZONE


class _GetRealGoldMixin(object):
    def get_real_gold(self, gold, logs):
        for log in logs:
            gold -= log.gold

        if gold < 0:
            gold = 0
        return gold


class HangObject(_GetRealGoldMixin):
    __slots__ = ['city_id', 'start_time', 'logs', 'finished', 'passed_time', 'max_time']
    def __init__(self, city_id, start_time, logs):
        self.city_id = city_id
        self.start_time = start_time
        self.logs = logs

        now = arrow.utcnow().timestamp
        time_diff = now - self.start_time

        self.max_time = BATTLES[self.city_id].total_hours * 3600
        self.finished = time_diff >= self.max_time

        self.passed_time = self.max_time if self.finished else time_diff


    def _utc_to_HH_mm(self, timestamp):
        return arrow.get(timestamp).to(TIME_ZONE).format('HH:mm')


    def make_logs(self):
        logs = []

        if self.finished:
            inserted_timestamp = self.start_time + self.max_time
        else:
            inserted_timestamp = 0

        for log in self.logs:
            if inserted_timestamp and inserted_timestamp < log.timestamp:
                # 插入 时间满 的log
                text = PLUNDER_LOG_TEMPLATE[3].format(self._utc_to_HH_mm(inserted_timestamp))
                logs.append(text)
                inserted_timestamp = 0
                continue

            template = PLUNDER_LOG_TEMPLATE[log.tp]
            hh_mm = self._utc_to_HH_mm(log.timestamp)

            if log.tp == 1:
                text = template.format(hh_mm, log.who, log.gold, log.item_text)
            else:
                # tp == 2
                text = template.format(hh_mm, log.who)

            logs.append(text)

        return logs


    def make_hang_notify(self):
        msg = HangNotify()
        msg.city_id = self.city_id
        msg.start_time = self.start_time
        msg.finished = self.finished

        gold = self.passed_time / 15 * BATTLES[self.city_id].normal_gold
        msg.gold = self.get_real_gold(gold, self.logs)

        logs = self.make_logs()
        msg.logs.extend(logs)
        return msg



class Affairs(_GetRealGoldMixin):
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.mongo_affairs = MongoAffairs.objects.get(id=char_id)
        except DoesNotExist:
            self.mongo_affairs = MongoAffairs(id=char_id)
            self.mongo_affairs.opened = []
            self.mongo_affairs.hang_city_id = 0
            self.mongo_affairs.hang_start_at = 0
            self.mongo_affairs.logs = []
            self.mongo_affairs.save()


    def open_city(self, city_id):
        # 开启城镇
        if city_id not in BATTLES:
            return False

        if city_id in self.mongo_affairs.opened:
            return False

        self.mongo_affairs.opened.append(city_id)
        self.mongo_affairs.save()
        self.send_city_notify()
        return True



    def start_hang(self, city_id):
        if city_id not in BATTLES:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Start Hang",
                "hang at none exist city id {0}".format(city_id)
            )

        if city_id not in self.mongo_affairs.opened:
            raise SanguoException(
                errormsg.INVALID_OPERATE,
                self.char_id,
                "Start Hang",
                "city id {0} not opened".format(city_id)
            )

        if self.mongo_affairs.hang_city_id:
            # 上次有挂机，先结算
            drop_msg = self.get_hang_reward(auto_start=False)
        else:
            drop_msg = None

        self.mongo_affairs.hang_city_id = city_id
        self.mongo_affairs.hang_start_at = arrow.utcnow().timestamp
        self.mongo_affairs.logs = []
        self.mongo_affairs.save()

        self.send_hang_notify()
        return drop_msg


    def get_hang_reward(self, auto_start=True):
        """立即保存掉落，并且返回attachment消息"""
        if not self.mongo_affairs.hang_city_id:
            raise SanguoException(
                errormsg.HANG_NOT_EXIST,
                self.char_id,
                "Get Hang Reward",
                "hang not exist"
            )

        ho = HangObject(self.mongo_affairs.hang_city_id, self.mongo_affairs.hang_start_at, self.mongo_affairs.logs)

        battle_data = BATTLES[self.mongo_affairs.hang_city_id]

        percent = ho.passed_time / float(ho.max_time)
        for _pre, _add in HANG_REWARD_ADDITIONAL:
            if percent >= _pre:
                break
        else:
            _add = 1

        char = Char(self.char_id)
        vip_level = char.mc.vip
        vip_add = VIP_DEFINE[vip_level].hang_addition

        passed_time = int(ho.passed_time * _add * (1 + vip_add / 100.0))

        reward_gold = passed_time / 15 * battle_data.normal_gold
        reward_gold = self.get_real_gold(reward_gold, self.mongo_affairs.logs)

        reward_exp = passed_time / 15 * battle_data.normal_exp

        if battle_data.normal_drop:
            drops = get_drop([int(i) for i in battle_data.normal_drop.split(',')], multi=passed_time/15)
        else:
            drops = make_standard_drop_from_template()

        drops['exp'] += reward_exp
        drops['gold'] += reward_gold

        resource = Resource(self.char_id, "Hang Reward")
        standard_drop = resource.add(**drops)

        if auto_start:
            # 领取奖励后自动开始
            self.start_hang(self.mongo_affairs.hang_city_id)

        return standard_drop_to_attachment_protomsg(standard_drop)



    def got_plundered(self, self_win, who):
        pass




    def send_city_notify(self):
        msg = CityNotify()
        for cid in CITY_IDS:
            city = msg.cities.add()
            city.id = cid
            city.status = CityMsg.OPEN if cid in self.mongo_affairs.opened else CityMsg.CLOSE

        publish_to_char(self.char_id, pack_msg(msg))


    def send_hang_notify(self):
        if not self.mongo_affairs.hang_city_id:
            return

        ho = HangObject(self.mongo_affairs.hang_city_id, self.mongo_affairs.hang_start_at, self.mongo_affairs.logs)
        msg = ho.make_hang_notify()
        publish_to_char(self.char_id, pack_msg(msg))


