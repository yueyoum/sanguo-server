"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

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


# class SaveAndDeleteEquipmentTest(TransactionTestCase):
#     def setUp(self):
#         char = char_initialize(1, 1, 'a')
#         self.char_id = char.id
#         c = MongoChar.objects.only('equips').get(id=self.char_id)
#         self.original_equip_amount = len(c.equips)
#
#     def tearDown(self):
#         app_test_helper._teardown()
#
#     def test_save_equip(self):
#         equip = generate_and_save_equip(1, 1, self.char_id)
#         char = MongoChar.objects.only('equips').get(id=self.char_id)
#         self.assertEqual(len(char.equips), 1 + self.original_equip_amount)
#         self.assertTrue(int(equip.id) in char.equips)
#
#         MongoChar.objects(id=self.char_id).update_one(
#             add_to_set__equips=equip.id
#         )
#
#         char.reload()
#         self.assertEqual(len(char.equips), 1 + self.original_equip_amount)
#
#         app_test_helper._mongo_teardown_func()
#
#     def test_remove_equip(self):
#         equip = generate_and_save_equip(1, 1, self.char_id)
#         char = MongoChar.objects.only('equips').get(id=self.char_id)
#         self.assertEqual(len(char.equips), 1 + self.original_equip_amount)
#
#         delete_equip(equip.id)
#         char.reload()
#         self.assertEqual(len(char.equips), 0 + self.original_equip_amount)
#         app_test_helper._mongo_teardown_func()
#
#
# class StrengthEquipmentTest(TransactionTestCase):
#     def setUp(self):
#         char = char_initialize(1, 1, 'a')
#         self.char_id = char.id
#         self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))
#         self.item = Item(self.char_id)
#
#     def tearDown(self):
#         app_test_helper._teardown()
#
#     def _prepare_equip(self):
#         self.equip_ids = []
#         for i in range(3):
#             eid = self.item.equip_add(i+1)
#             self.equip_ids.append(eid)
#
#     def _strength(self, _id, ret=0):
#         req = protomsg.StrengthEquipRequest()
#         req.session = self.session
#         req.id = _id
#
#         data = app_test_helper.pack_data(req)
#         res = app_test_helper.make_request('/equip/strengthen/', data)
#         msgs = app_test_helper.unpack_data(res)
#
#         for id_of_msg, _, msg in msgs:
#             if id_of_msg == RESPONSE_NOTIFY_TYPE["StrengthEquipResponse"]:
#                 data = protomsg.StrengthEquipResponse()
#                 data.ParseFromString(msg)
#                 self.assertEqual(data.ret, ret)
#
#     # def test_normal_strength(self):
#     #     self._prepare_equip()
#     #     _id = self.equip_ids[0]
#     #
#     #     c = Char(self.char_id)
#     #     c.update(gold=9999)
#     #
#     #     self._strength(_id)
#
#     # def test_not_enough_gold(self):
#     #     self._prepare_equip()
#     #     _id = self.equip_ids[0]
#     #     self._strength(_id, 10)
#
#     def test_none_exists_strength(self):
#         self._strength(999, 2)
#


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



#
# class SellEquipmentTest(TransactionTestCase):
#     def setUp(self):
#         char = char_initialize(1, 1, 'a')
#         self.char_id = char.id
#         self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))
#         self.item = Item(self.char_id)
#
#     def tearDown(self):
#         app_test_helper._teardown()
#
#     def _prepare_equip(self):
#         self.equip_ids = []
#         for i in range(3):
#             eid = self.item.equip_add(i+1)
#             self.equip_ids.append(eid)
#
#
#     def _sell(self, _id, ret=0):
#         req = protomsg.SellEquipRequest()
#         req.session = self.session
#         req.ids.append(_id)
#
#         data = app_test_helper.pack_data(req)
#         res = app_test_helper.make_request('/equip/sell/', data)
#         msgs = app_test_helper.unpack_data(res)
#
#         for id_of_msg, _, msg in msgs:
#             if id_of_msg == RESPONSE_NOTIFY_TYPE["SellEquipResponse"]:
#                 data = protomsg.SellEquipResponse()
#                 data.ParseFromString(msg)
#                 self.assertEqual(data.ret, ret)
#
#     def test_normal_sell(self):
#         self._prepare_equip()
#         self._sell(self.equip_ids[0])
#
#
#     def test_none_exists_strength(self):
#         self._sell(999, 2)
#

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


#
# class GemTest(TransactionTestCase):
#     def setUp(self):
#         char = char_initialize(1, 1, 'a')
#         gems = (
#             (49, 4),
#             (48, 3),
#
#             (47, 4),
#             (46, 3),
#         )
#         item = Item(char.id)
#         item.gem_add(gems)
#         self.session = crypto.encrypt('1:1:{0}'.format(char.id))
#         self.char_id = char.id
#
#     def tearDown(self):
#         app_test_helper._teardown()
#
#
#     def _merge(self, _id, ret=0):
#         req = protomsg.MergeGemRequest()
#         req.session = self.session
#         req.id = _id
#
#         data = app_test_helper.pack_data(req)
#         res = app_test_helper.make_request('/gem/merge/', data)
#         msgs = app_test_helper.unpack_data(res)
#
#         for id_of_msg, len_of_msg, msg in msgs:
#             if id_of_msg == RESPONSE_NOTIFY_TYPE["MergeGemResponse"]:
#                 data = protomsg.MergeGemResponse()
#                 data.ParseFromString(msg)
#                 self.assertEqual(data.ret, ret)
#
#     def test_normal_merge(self):
#         self._merge(47)
#
#     def test_non_exist_merge(self):
#         self._merge(999, 2)
#
#     def test_not_enough_merge(self):
#         self._merge(46, 15)
#

