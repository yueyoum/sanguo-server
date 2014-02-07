# -*- coding: utf-8 -*-
from core.character import char_initialize
from utils import crypto

__author__ = 'Wang Chao'
__date__ = '1/23/14'

from django.test import TransactionTestCase

from utils import app_test_helper

from core.heropanel import HeroPanel
import protomsg


class HeroPanelTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))

        self.panel = HeroPanel(self.char_id)


    def tearDown(self):
        app_test_helper._teardown()

    def test_get(self):
        req = protomsg.GetHeroRequest()
        req.session = self.session
        req.id = 1

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/hero/get/', data)
        msgs = app_test_helper.unpack_data(res)

    def test_refresh(self):
        req = protomsg.GetHeroRefreshRequest()
        req.session = self.session
        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/heropanel/refresh/', data)
        msg = app_test_helper.unpack_data(res)
