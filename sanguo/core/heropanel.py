# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/23/14'

import random
import arrow

from mongoengine import DoesNotExist
from core.mongoscheme import MongoHeroPanel, MongoEmbeddedHeroPanelHero
from core.counter import Counter
from core.exception import SanguoException, CounterOverFlow
from core.hero import save_hero
from core.resource import Resource
from core.task import Task
from core.msgpipe import publish_to_char
from utils import pack_msg
from preset import errormsg
import protomsg
from preset.settings import (
    GET_HERO_QUALITY_ONE_POOL,
    GET_HERO_QUALITY_TWO_POOL,
    GET_HERO_QUALITY_THREE_POOL,
    GET_HERO_TWO_QUALITY_ONE_HEROS,
    GET_HERO_COST,
    GET_HERO_REFRESH,
    GET_HERO_FORCE_REFRESH_COST,
    GET_HERO_QUALITY_ONE_PROB,
)

MERGED_OTHER_HERO_POOL = []
MERGED_OTHER_HERO_POOL.extend(GET_HERO_QUALITY_TWO_POOL)
MERGED_OTHER_HERO_POOL.extend(GET_HERO_QUALITY_THREE_POOL)


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
        if self.all_opended():
            # 如果全部翻开了，就可以立即刷新
            return 0

        last_refresh = self.panel.last_refresh

        time_passed = arrow.utcnow().timestamp - last_refresh
        seconds = GET_HERO_REFRESH - time_passed
        if seconds < 0:
            seconds = 0
        return seconds

    @property
    def free_times(self):
        # 翻卡牌的免费次数
        c = Counter(self.char_id, 'gethero')
        return c.remained_value


    @property
    def open_times(self):
        times = 0
        for v in self.panel.panel.values():
            if v.opened:
                times += 1
        return times


    def none_opened_heros(self):
        heros = []
        for k, v in self.panel.panel.iteritems():
            if not v.opened:
                heros.append((k, v))
        return heros


    def all_closed(self):
        for v in self.panel.panel.values():
            if v.opened:
                return False
        return True

    def all_opended(self):
        for v in self.panel.panel.values():
            if not v.opened:
                return False
        return True

    def get_hero_cost(self, incr=False):
        counter = Counter(self.char_id, 'gethero')

        if incr:
            try:
                counter.incr()
                return 0
            except CounterOverFlow:
                return GET_HERO_COST
        else:
            if counter.remained_value > 0:
                return 0
            return GET_HERO_COST

    def open(self, _id):
        if str(_id) not in self.panel.panel:
            raise SanguoException(
                errormsg.HEROPANEL_SOCKET_NOT_EXIST,
                self.char_id,
                "HeroPanel Open",
                "HeroPanel Socket {0} not exist".format(_id)
            )

        if self.panel.panel[str(_id)].opened:
            # raise SanguoException(
            #     errormsg.HEROPANEL_SOCKET_ALREADY_OPENED,
            #     self.char_id,
            #     "HeroPanel Open",
            #     "HeroPanel Socket {0} already opended".format(_id)
            # )
            return None

        none_opended_heros = self.none_opened_heros()
        if not none_opended_heros:
            raise SanguoException(
                errormsg.HEROPANEL_ALL_OPENED,
                self.char_id,
                "HeroPanel Open",
                "all opened."
            )

        none_opened_good_hero = None
        none_opened_other_heros = []
        for k, v in none_opended_heros:
            if v.good:
                none_opened_good_hero = (k, v)
                continue

            none_opened_other_heros.append((k, v))

        using_sycee = self.get_hero_cost(incr=True)

        resource = Resource(self.char_id, "HeroPanel Open")
        with resource.check(sycee=-using_sycee):
            if none_opened_good_hero:
                # 还没有取到甲卡
                prob = GET_HERO_QUALITY_ONE_PROB[self.open_times + 1]
                if random.randint(1, 100) <= prob:
                    # 取得甲卡
                    socket_id, hero = none_opened_good_hero
                else:
                    socket_id, hero = random.choice(none_opened_other_heros)
            else:
                socket_id, hero = random.choice(none_opened_other_heros)

            self.panel.panel[str(_id)], self.panel.panel[socket_id] = self.panel.panel[socket_id], self.panel.panel[str(_id)]

            self.panel.panel[str(_id)].opened = True
            self.panel.save()
            save_hero(self.char_id, hero.oid)

        self.send_notify()

        Task(self.char_id).trig(7)
        return hero.oid


    def refresh(self):
        if self.all_opended():
            # 所有卡都翻完了。直接刷新
            self.panel = self.make_new_panel()
            self.send_notify()
            return

        if self.refresh_seconds > 0:
            # 免费刷新还在冷却，只能用元宝刷新，不重置免费刷新时间
            resouce = Resource(self.char_id, "HeroPanel Refresh")
            with resouce.check(sycee=-GET_HERO_FORCE_REFRESH_COST):
                self.panel = self.make_new_panel(reset_time=False)
            self.send_notify()
            return

        # 可以用免费刷新
        self.panel = self.make_new_panel()
        self.send_notify()


    def make_new_panel(self, reset_time=True):
        panel = MongoHeroPanel()
        panel.id = self.char_id
        panel.got_good_hero = False

        if reset_time:
            panel.last_refresh = arrow.utcnow().timestamp
        else:
            panel.last_refresh = self.panel.last_refresh

        good_hero_amount = 1
        if random.randint(1, 100) <= GET_HERO_TWO_QUALITY_ONE_HEROS:
            good_hero_amount = 2

        heros = []

        while len(heros) < good_hero_amount:
            choose_good_hero = random.choice(GET_HERO_QUALITY_ONE_POOL)
            if choose_good_hero not in heros:
                heros.append(choose_good_hero)

        while len(heros) < 6:
            choose_other_hero = random.choice(MERGED_OTHER_HERO_POOL)
            if choose_other_hero not in heros:
                heros.append(choose_other_hero)

        embedded_hero_objs = []
        embedded_hero_objs.append(
            MongoEmbeddedHeroPanelHero(oid=heros[0], good=True, opened=False)
        )
        for h in heros[1:]:
            embedded_hero_objs.append(
                MongoEmbeddedHeroPanelHero(oid=h, good=False, opened=False)
            )

        random.shuffle(embedded_hero_objs)

        for index, i in enumerate(embedded_hero_objs):
            panel.panel[str(index+1)] = i

        panel.save()
        return panel


    def send_notify(self):
        msg = protomsg.GetHeroPanelNotify()
        msg.refresh_seconds = self.refresh_seconds
        msg.free_times = self.free_times
        msg.open_sycee = self.get_hero_cost(incr=False)
        msg.refresh_sycee = GET_HERO_FORCE_REFRESH_COST

        for k, v in self.panel.panel.iteritems():
            msg_s = msg.sockets.add()
            msg_s.id = int(k)
            msg_s.hero_id = v.oid
            msg_s.opened = v.opened

        publish_to_char(self.char_id, pack_msg(msg))

