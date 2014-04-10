# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'

from django.test import TestCase

from utils import app_test_helper
from core.character import char_initialize
from core.hero import save_hero, Hero
import protomsg

from libs import crypto


def tearDown():
    app_test_helper._teardown()


class HeroTest(TestCase):
    def setUp(self):
        char = char_initialize(1, 1, 1, 'a')
        self.char_id = 1
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))

        id_range = save_hero(self.char_id, 1)
        self.hero_id = id_range[0]


    def _step_up(self, _id, ret=0):
        req = protomsg.HeroStepUpRequest()
        req.session = self.session
        req.id = _id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/hero/stepup/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == protomsg.RESPONSE_NOTIFY_TYPE["HeroStepUpResponse"]:
                data = protomsg.HeroStepUpResponse()
                data.ParseFromString(msg)
                # self.assertEqual(data.ret, ret)


    # def test_none_exist_step_up(self):
    #     self._step_up(999, 2)

    def test_normal_step_up(self):
        self._step_up(self.hero_id)

        # h = Hero(self.hero_id)
        # self.assertEqual(h.step, 2)
