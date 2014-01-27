# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/23/14'

import random
from mongoengine import DoesNotExist
from apps.hero.models import Hero

from core.mongoscheme import MongoEmbeddedPanelHero, MongoHeroPanel
from core.counter import Counter
from core.exception import InvalidOperate, SyceeNotEnough
from core.hero import save_hero
from core.character import Char

from core.msgpipe import publish_to_char
from utils import pack_msg
from utils import timezone


import protomsg

REFRESH = 60
REFRESH_COST_SYCEE = 1
GETHERO_COST_SYCEE = 1
class HeroPanel(object):
    AMOUNT = 6
    def __init__(self, char_id):
        self.char_id = char_id
        try:
            self.panel = MongoHeroPanel.objects.get(id=self.char_id)
        except DoesNotExist:
            self.panel = self.make_new_panel()


    @property
    def refresh_seconds(self):
        # 还有多少秒可以免费刷新
        last_refresh = self.panel.last_refresh

        time_passed = timezone.utc_timestamp() - last_refresh
        seconds = REFRESH - time_passed
        if seconds < 0:
            seconds = 0
        return seconds

    @property
    def free_times(self):
        # 翻卡牌的免费次数
        c = Counter(self.char_id, 'gethero')
        times = c.remained_value
        return times if times >=0 else 0

    @property
    def new_start(self):
        if self.panel.started:
            return False

        if not self.all_closed():
            return False

        return True


    def all_closed(self):
        for v in self.panel.panel.values():
            if v.opended:
                return False
        return True

    def all_opended(self):
        for v in self.panel.panel.values():
            if not v.opended:
                return False

        return True


    def start(self):
        self.panel.started = True
        self.panel.save()
        self.send_notify()


    def open(self, _id):
        if str(_id) not in self.panel.panel:
            raise InvalidOperate("Get Hero, Open: Char {0} Try to open a NONE exist socket id: {1}".format(
                self.char_id, _id
            ))

        # TODO   检查武将包裹是否满了

        if self.free_times == 0:
            # 使用元宝
            char = Char(self.char_id)
            cache_char = char.cacheobj
            if cache_char.sycee < GETHERO_COST_SYCEE:
                raise SyceeNotEnough()

            char.update(sycee=-GETHERO_COST_SYCEE)
        else:
            c = Counter(self.char_id, 'gethero')
            c.incr()

        if self.panel.panel[str(_id)].opended:
            raise InvalidOperate("HeroPanel Open: Char {0} Try to open an already opened socket {1}".format(
                self.char_id, _id
            ))

        hero_id = self.panel.panel[str(_id)].hero_id
        self.panel.panel[str(_id)].opended = True
        self.panel.save()

        save_hero(self.char_id, hero_id)
        self.send_notify()


    def refresh(self):
        if self.all_opended():
            # 重新开始，不重置刷新功能
            self.panel = self.make_new_panel(reset_time=False)
            self.send_notify()
            return

        if self.refresh_seconds > 0:
            # 免费刷新还在冷却，只能用元宝刷新，不重置免费刷新时间
            char = Char(self.char_id)
            cache_char = char.cacheobj
            if cache_char.sycee < REFRESH_COST_SYCEE:
                raise SyceeNotEnough()

            char.update(sycee=-REFRESH_COST_SYCEE)

            self.panel = self.make_new_panel(reset_time=False)
            self.send_notify()
            return

        # 可以用免费刷新
        self.panel = self.make_new_panel()
        self.send_notify()


    def make_new_panel(self, reset_time=True):
        # FIXME 选择武将
        all_heros = Hero.all()

        choosing = []
        for i in all_heros.keys():
            if len(choosing) >= self.AMOUNT:
                break
            if i not in choosing:
                choosing.append(i)

        random.shuffle(choosing)

        panel = MongoHeroPanel()
        panel.id = self.char_id
        panel.started = False

        if reset_time:
            panel.last_refresh = timezone.utc_timestamp()
        else:
            panel.last_refresh = self.panel.last_refresh


        for index, hid in enumerate(choosing):
            ph = MongoEmbeddedPanelHero()
            ph.hero_id = hid
            ph.opended = False

            panel.panel[str(index + 1)] = ph

        panel.save()
        return panel

    def send_notify(self):
        msg = protomsg.GetHeroPanelNotify()
        msg.refresh_seconds = self.refresh_seconds
        msg.free_times = self.free_times
        msg.open_sycee = GETHERO_COST_SYCEE
        msg.refresh_sycee = REFRESH_COST_SYCEE
        msg.new_start = self.new_start

        for k, v in self.panel.panel.iteritems():
            socket = msg.sockets.add()
            socket.id = int(k)

            if msg.new_start:
                hero_id = v.hero_id
            else:
                hero_id = v.hero_id if v.opended else 0

            socket.hero_id = hero_id

        publish_to_char(self.char_id, pack_msg(msg))

