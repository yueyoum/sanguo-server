# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'


from django.test import TestCase
import protomsg
from protomsg import RESPONSE_NOTIFY_TYPE

from utils import app_test_helper
from utils import crypto

from core.character import char_initialize

from core.item import Item
from core.character import Char

def teardown():
    app_test_helper._teardown()



class EquipmentStepUpTest(TestCase):
    def setUp(self):
        char_initialize(1, 1, 1, 'a')
        self.char_id = 1
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))
        self.item = Item(self.char_id)
        self.equip_id = self.item.equip_add(1)

    def tearDown(self):
        app_test_helper._teardown()

    def _step_up(self, _id, ret=0):
        req = protomsg.StepUpEquipRequest()
        req.session = self.session
        req.id = _id
        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/equip/stepup/', data)
        msgs = app_test_helper.unpack_data(res)
        for a, b, c in msgs:
            if a == protomsg.RESPONSE_NOTIFY_TYPE["StepUpEquipResponse"]:
                data = protomsg.StepUpEquipResponse()
                data.ParseFromString(c)
                self.assertEqual(data.ret, ret)

    def test_none_exist(self):
        self._step_up(999, 2)

    # def test_error_step_up(self):
    #     self._step_up(self.equip_id, 16)

    def test_normal_step_up(self):
        item = Item(self.char_id)
        item.stuff_add([(1, 1), (2, 1)])
        self._step_up(self.equip_id)



class EmbedGemTest(TestCase):
    def setUp(self):
        char_initialize(1, 1, 1, 'a')
        self.char_id = 1
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))

        item = Item(self.char_id)
        eid = item.equip_add(1)
        self.equip_id = eid

        gems = [(1, 10), (2, 1)]
        item.gem_add(gems)

    def tearDown(self):
        app_test_helper._teardown()


    def _embed(self, equip_id, hole_id, gem_id, ret=0):
        if gem_id == 0:
            req = protomsg.UnEmbedGemRequest()
            url = '/equip/unembed/'
            response_name = "UnEmbedGemResponse"
        else:
            req = protomsg.EmbedGemRequest()
            req.gem_id = gem_id
            url = '/equip/embed/'
            response_name = "EmbedGemResponse"

        req.session = self.session
        req.equip_id = equip_id
        req.hole_id = hole_id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request(url, data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, _, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE[response_name]:
                data = getattr(protomsg, response_name)()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def test_normal_embed(self):
        self._embed(self.equip_id, 1, 1)

    def test_normal_unembed(self):
        self._embed(self.equip_id, 1, 1)
        self._embed(self.equip_id, 1, 0)

    def test_error_embed(self):
        self._embed(999, 999, 1, 2)
        self._embed(999, 1, 1, 2)
        self._embed(self.equip_id, 1, 999, 2)


