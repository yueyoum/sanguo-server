# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/23/14'

import random

from django.conf import settings

from mongoengine import DoesNotExist

from core.mongoscheme import MongoHeroPanel
from core.counter import Counter
from core.exception import InvalidOperate, SyceeNotEnough
from core.hero import save_hero
from core.character import Char

from core.msgpipe import publish_to_char
from utils import pack_msg
from utils import timezone

from preset.data import HERO_GET_BY_QUALITY, HERO_GET_BY_QUALITY_NOT_EQUAL, CHARINIT


import protomsg

REFRESH = 60
GETHERO_COST_SYCEE = 300
REFRESH_COST_SYCEE = 100
MAX_AMOUNT = 6

GET_GOOD_HERO_PROB = {
    1: 1,
    2: 3,
    3: 6,
    4: 12,
    5: 30,
    6: 100,
}


class HeroPanel(object):
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

    @property
    def open_times(self):
        times = 0
        for v in self.panel.panel.values():
            if v:
                times += 1
        return times

    def has_got_good_hero(self):
        return self.panel.good_hero == 0


    def all_closed(self):
        for v in self.panel.panel.values():
            if v:
                return False
        return True

    def all_opended(self):
        for v in self.panel.panel.values():
            if v == 0:
                return False

        return True


    def start(self):
        self.panel.started = True
        self.panel.save()
        self.send_notify()


    def open(self, _id):
        if settings.IS_GUIDE_SERVER:
            hero_id = CHARINIT.extra_hero
        else:
            if self.all_opended():
                raise InvalidOperate("Get Hero, Open: Char {0} Try to open {1}. But All Opened".format(self.char_id, _id))

            if str(_id) not in self.panel.panel:
                raise InvalidOperate("Get Hero, Open: Char {0} Try to open a NONE exist socket id: {1}".format(
                    self.char_id, _id
                ))

            if self.panel.panel[str(_id)]:
                raise InvalidOperate("HeroPanel Open: Char {0} Try to open an already opened socket {1}".format(
                    self.char_id, _id
                ))
            if self.free_times == 0:
                # 使用元宝
                char = Char(self.char_id)
                cache_char = char.cacheobj
                if cache_char.sycee < GETHERO_COST_SYCEE:
                    raise SyceeNotEnough()

                char.update(sycee=-GETHERO_COST_SYCEE, des='HeroPanel Open')
            else:
                c = Counter(self.char_id, 'gethero')
                c.incr()

            if self.has_got_good_hero():
                hero_id = random.choice(self.panel.other_heros)
                self.panel.other_heros.remove(hero_id)
            else:
                prob = GET_GOOD_HERO_PROB[self.open_times + 1]
                if random.randint(1, 100) <= prob:
                    # 取得甲卡
                    hero_id = self.panel.good_hero
                    self.panel.good_hero = 0
                else:
                    hero_id = random.choice(self.panel.other_heros)
                    self.panel.other_heros.remove(hero_id)

            self.panel.panel[str(_id)] = hero_id
            self.panel.save()

        save_hero(self.char_id, hero_id)
        self.send_notify()
        return hero_id

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

            char.update(sycee=-REFRESH_COST_SYCEE, des='HeroPanel Refresh')

            self.panel = self.make_new_panel(reset_time=False)
            self.send_notify()
            return

        # 可以用免费刷新
        self.panel = self.make_new_panel()
        self.send_notify()


    def make_new_panel(self, reset_time=True):
        panel = MongoHeroPanel()
        panel.id = self.char_id
        panel.started = False

        good_hero_amount = 1
        if random.randint(1, 100) <= 4:
            good_hero_amount = 2
        good_hero = HERO_GET_BY_QUALITY(1, good_hero_amount)

        panel.good_hero = good_hero.keys()[0]
        if good_hero_amount == 2:
            panel.other_heros.append(good_hero.keys()[1])



        other_hero_amount = MAX_AMOUNT - good_hero_amount
        other_heros = HERO_GET_BY_QUALITY_NOT_EQUAL(1, other_hero_amount)

        panel.other_heros.extend(other_heros.keys())


        if reset_time:
            panel.last_refresh = timezone.utc_timestamp()
        else:
            panel.last_refresh = self.panel.last_refresh

        for i in range(MAX_AMOUNT):
            panel.panel[str(i+1)] = 0

        panel.save()
        return panel

    def send_notify(self):
        msg = protomsg.GetHeroPanelNotify()
        msg.refresh_seconds = self.refresh_seconds
        msg.free_times = self.free_times
        msg.open_sycee = GETHERO_COST_SYCEE
        msg.refresh_sycee = REFRESH_COST_SYCEE
        msg.new_start = self.new_start

        index = 0
        all_panel_heros = []
        if self.panel.good_hero:
            all_panel_heros.append(self.panel.good_hero)

        all_panel_heros.extend(self.panel.other_heros)

        for k, v in self.panel.panel.iteritems():
            socket = msg.sockets.add()
            socket.id = int(k)

            if msg.new_start:
                hero_id = all_panel_heros[index]
                index += 1
            else:
                hero_id = v

            socket.hero_id = hero_id

        publish_to_char(self.char_id, pack_msg(msg))

