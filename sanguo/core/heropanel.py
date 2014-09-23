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
            self.panel = self.make_new_panel(is_first_time=True)


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

    def has_got_good_hero(self):
        for v in self.panel.panel.values():
            if v.opened and v.good:
                return True
        return False

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

        if self.all_opended():
            raise SanguoException(
                errormsg.HEROPANEL_ALL_OPENED,
                self.char_id,
                "HeroPanel Open",
                "all opened."
            )

        none_opened_heros = self.none_opened_heros()
        none_opened_other_heros = [(socket_id, h) for socket_id, h in none_opened_heros if not h.good]

        def _random_get():
            if none_opened_other_heros:
                return random.choice(none_opened_other_heros)
            return random.choice(none_opened_heros)

        using_sycee = self.get_hero_cost(incr=True)

        resource = Resource(self.char_id, "HeroPanel Open")
        with resource.check(sycee=-using_sycee):
            if not self.has_got_good_hero():
                # 还没有取到甲卡
                if self.panel.refresh_times == 0:
                    # 新角色第一次抽卡，给好卡
                    prob = 100
                else:
                    prob = GET_HERO_QUALITY_ONE_PROB[self.open_times + 1]

                if random.randint(1, 100) <= prob:
                    # 取得甲卡
                    for k, v in none_opened_heros:
                        if v.good:
                            socket_id, hero = k, v
                            break
                    else:
                        socket_id, hero = _random_get()
                else:
                    socket_id, hero = _random_get()
            else:
                socket_id, hero = _random_get()

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


    def make_new_panel(self, reset_time=True, is_first_time=False):
        panel = MongoHeroPanel()
        panel.id = self.char_id

        if reset_time:
            panel.last_refresh = arrow.utcnow().timestamp
        else:
            panel.last_refresh = self.panel.last_refresh

        if is_first_time:
            panel.refresh_times = 0
            heros = self._first_time_hero_lists()
        else:
            panel.refresh_times += 1
            heros = self._other_times_hero_list()

        embedded_hero_objs = []
        for oid, good in heros:
            embedded_hero_objs.append(
                MongoEmbeddedHeroPanelHero(oid=oid, good=good, opened=False)
            )

        for index, i in enumerate(embedded_hero_objs):
            panel.panel[str(index+1)] = i

        panel.save()
        return panel


    def _first_time_hero_lists(self):
        """
        新手第一次抽奖的武将包需要设定为 2张随机金卡（甲），3张银卡（乙），1张铜卡（丙）。
        武将从设定的武将池里生成。
        新手引导的第一次免费抽奖，直接2张金卡中选择一张抽中。
        """
        quality_one_heros = random.sample(GET_HERO_QUALITY_ONE_POOL, 2)
        quality_two_heros = random.sample(GET_HERO_QUALITY_TWO_POOL, 3)
        quality_three_heros = random.sample(GET_HERO_QUALITY_THREE_POOL, 1)

        heros = []

        for h in quality_one_heros:
            heros.append((h, True))

        for h in quality_two_heros:
            heros.append((h, False))

        for h in quality_three_heros:
            heros.append((h, False))

        random.shuffle(heros)
        return heros


    def _other_times_hero_list(self):
        good_hero_amount = 1
        if random.randint(1, 100) <= GET_HERO_TWO_QUALITY_ONE_HEROS:
            good_hero_amount = 2

        quality_one_heros = random.sample(GET_HERO_QUALITY_ONE_POOL, good_hero_amount)
        quality_other_heros = random.sample(MERGED_OTHER_HERO_POOL, 6-good_hero_amount)

        heros = []

        for h in quality_one_heros:
            heros.append((h, True))

        for h in quality_other_heros:
            heros.append((h, False))

        random.shuffle(heros)
        return heros


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

