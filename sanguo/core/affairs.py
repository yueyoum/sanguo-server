# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-9-11'

import arrow
from mongoengine import DoesNotExist

from django.conf import settings

from core.mongoscheme import MongoAffairs, MongoEmbeddedHangLog, MongoStage
from core.exception import SanguoException
from core.attachment import get_drop, make_standard_drop_from_template, standard_drop_to_attachment_protomsg, standard_drop_to_readable_text
from core.resource import Resource
from core.character import Char
from core.achievement import Achievement

from core.msgpipe import publish_to_char

from utils import pack_msg

from preset import errormsg
from preset.data import BATTLES, VIP_FUNCTION
from preset.settings import (
    PLUNDER_LOG_TEMPLATE,
    HANG_REWARD_ADDITIONAL,
    PLUNDER_LOG_MAX_AMOUNT,
    PLUNDER_GET_DROPS_MINUTES,
)

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
    __slots__ = ['city_id', 'start_time', 'logs', 'finished', 'passed_time', 'max_time', 'gold']
    def __init__(self, city_id, start_time, logs):
        self.city_id = city_id
        self.start_time = start_time
        self.logs = logs

        now = arrow.utcnow().timestamp
        time_diff = now - self.start_time

        self.max_time = BATTLES[self.city_id].total_hours * 3600
        self.finished = time_diff >= self.max_time

        self.passed_time = self.max_time if self.finished else time_diff

        gold = self.passed_time / 15 * BATTLES[self.city_id].normal_gold
        self.gold = self.get_real_gold(gold, self.logs)


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

        msg.gold = self.gold

        logs = self.make_logs()
        msg.logs.extend(logs)
        return msg



def _get_opended_cities(char_id):
    from core.stage import Stage
    from preset.data import STAGES

    stages = Stage(char_id).stage.stages.keys()
    stages = [int(i) for i in stages]

    opened = set()
    for sid in stages:
        this_stage = STAGES[sid]
        if this_stage.battle_end:
            opened.add(this_stage.battle)

    opened = list(opened)
    opened.sort()
    return opened


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

        self.set_default_value()


    def set_default_value(self):
        if self.mongo_affairs.opened:
            return

        opened = _get_opended_cities(self.char_id)
        if opened:
            self.mongo_affairs.opened = opened
            self.mongo_affairs.hang_city_id = opened[-1]
            self.mongo_affairs.hang_start_at = arrow.utcnow().timestamp
            self.mongo_affairs.save()


    def open_city(self, city_id):
        # 开启城镇

        # 因为从signals调用 open_city的时候
        # 对Affairs初始化时，会先把 1 开启，
        # 然后这里判断就是 没有开启……
        # 这里特殊处理

        if city_id == FIRST_CITY_ID and len(self.mongo_affairs.opened) == 1 and self.mongo_affairs.opened[0] == FIRST_CITY_ID:
            opened = True
        else:
            need_opened = []
            for cid in CITY_IDS:
                if cid > city_id:
                    # XXX 这里默认city_id是从小到大的！
                    break

                need_opened.append(cid)

            opened = False
            for cid in need_opened:
                if cid in self.mongo_affairs.opened:
                    continue

                self.mongo_affairs.opened.append(cid)
                opened = True

        self.mongo_affairs.save()
        self.send_city_notify()
        return opened


    def start_hang(self, city_id, get_reward=True):
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

        if get_reward:
            if self.mongo_affairs.hang_city_id:
                # 上次有挂机，先结算
                drop_msg = self.get_hang_reward(auto_start=False)
            else:
                drop_msg = None
        else:
            drop_msg = None

        self.mongo_affairs.hang_city_id = city_id
        self.mongo_affairs.hang_start_at = arrow.utcnow().timestamp
        self.mongo_affairs.logs = []
        self.mongo_affairs.save()

        self.send_hang_notify()
        return drop_msg


    def get_hang_obj(self):
        return HangObject(self.mongo_affairs.hang_city_id, self.mongo_affairs.hang_start_at, self.mongo_affairs.logs)


    def get_hang_reward(self, auto_start=True):
        """立即保存掉落，并且返回attachment消息"""
        if not self.mongo_affairs.hang_city_id:
            raise SanguoException(
                errormsg.HANG_NOT_EXIST,
                self.char_id,
                "Get Hang Reward",
                "hang not exist"
            )

        ho = self.get_hang_obj()
        battle_data = BATTLES[self.mongo_affairs.hang_city_id]

        percent = ho.passed_time / float(ho.max_time) * 100
        for _pre, _add in HANG_REWARD_ADDITIONAL:
            if percent >= _pre:
                break
        else:
            _add = 1

        char = Char(self.char_id)
        vip_level = char.mc.vip
        vip_add = VIP_FUNCTION[vip_level].hang_addition

        passed_time = int(ho.passed_time * _add * (1 + vip_add / 100.0))

        reward_gold = passed_time / 15 * battle_data.normal_gold
        reward_gold = self.get_real_gold(reward_gold, self.mongo_affairs.logs)

        reward_exp = passed_time / 15 * battle_data.normal_exp

        if battle_data.normal_drop:
            # 模拟损失物品
            drop_time = passed_time
            for log in self.mongo_affairs.logs:
                if log.tp == 1:
                    drop_time -= PLUNDER_GET_DROPS_MINUTES * 60

            drop_time_adjusted = max(int(passed_time * 0.25), drop_time)

            drops = get_drop([int(i) for i in battle_data.normal_drop.split(',')], multi=drop_time_adjusted/15)
        else:
            drops = make_standard_drop_from_template()

        drops['exp'] += reward_exp
        drops['gold'] += reward_gold

        resource = Resource(self.char_id, "Hang Reward")
        standard_drop = resource.add(**drops)

        if auto_start:
            # 领取奖励后自动开始
            self.start_hang(self.mongo_affairs.hang_city_id, get_reward=False)

        achievement = Achievement(self.char_id)
        achievement.trig(28, ho.passed_time / 3600)
        achievement.trig(29, reward_exp)

        return standard_drop_to_attachment_protomsg(standard_drop)



    def got_plundered(self, from_char_id, from_win, standard_drop):
        from_char = Char(from_char_id)
        from_name = from_char.mc.name

        if from_win:
            tp = 1
        else:
            tp = 2

        gold = standard_drop['gold']
        item_text = standard_drop_to_readable_text(standard_drop, sign='-')

        log = MongoEmbeddedHangLog()
        log.timestamp = arrow.utcnow().timestamp
        log.tp = tp
        log.who =from_name
        log.gold = gold
        log.item_text = item_text

        self.mongo_affairs.logs.append(log)

        if len(self.mongo_affairs.logs) > PLUNDER_LOG_MAX_AMOUNT:
            self.mongo_affairs.logs.pop(0)

        self.mongo_affairs.save()
        self.send_hang_notify()


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


