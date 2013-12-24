"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TransactionTestCase
import protomsg
from protomsg import RESPONSE_NOTIFY_TYPE

from utils import app_test_helper
from utils import crypto

from core.character import char_initialize
from core.equip import generate_and_save_equip, delete_equip
from core.mongoscheme import MongoChar
from core.gem import save_gem
from apps.character.models import Character


def teardown():
    app_test_helper._teardown()


class SaveAndDeleteEquipmentTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1,'a')
        self.char_id = char.id
        c = MongoChar.objects.only('equips').get(id=self.char_id)
        self.original_equip_amount = len(c.equips)
    
    def tearDown(self):
        app_test_helper._teardown()

    def test_save_equip(self):
        equip = generate_and_save_equip(1, 1, self.char_id)
        char = MongoChar.objects.only('equips').get(id=self.char_id)
        self.assertEqual(len(char.equips), 1 + self.original_equip_amount)
        self.assertTrue(int(equip.id) in char.equips)
        
        MongoChar.objects(id=self.char_id).update_one(
            add_to_set__equips = equip.id
        )
        
        char.reload()
        self.assertEqual(len(char.equips), 1 + self.original_equip_amount)
        
        app_test_helper._mongo_teardown_func()
    
    def test_remove_equip(self):
        equip = generate_and_save_equip(1, 1, self.char_id)
        char = MongoChar.objects.only('equips').get(id=self.char_id)
        self.assertEqual(len(char.equips), 1 + self.original_equip_amount)
        
        delete_equip(equip.id)
        char.reload()
        self.assertEqual(len(char.equips), 0 + self.original_equip_amount)
        app_test_helper._mongo_teardown_func()
        

class StrengthEquipmentTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1,'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))
        
        c = MongoChar.objects.only('equips').get(id=self.char_id)
        self.original_equip_amount = len(c.equips)
        
    def tearDown(self):
        app_test_helper._teardown()

    def _prepare_equip(self):
        self.equip_ids = []
        for i in range(3):
            e = generate_and_save_equip(1, 1, self.char_id)
            self.equip_ids.append(int(e.id))
        
    def _strength(self, _id, cost_ids, ret=0):
        req = protomsg.StrengthEquipRequest()
        req.session = self.session
        req.id = _id
        req.cost_ids.extend(cost_ids)
        
        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/equip/strengthen/', data)
        msgs = app_test_helper.unpack_data(res)
        
        for id_of_msg, _, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["StrengthEquipResponse"]:
                data = protomsg.StrengthEquipResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def test_normal_strength(self):
        self._prepare_equip()
        _id = self.equip_ids[0]
        cost_ids = self.equip_ids[1:]
        
        c = Character.objects.get(id=self.char_id)
        c.gold = 9999
        c.save()
        self._strength(_id, cost_ids)
        
        char = MongoChar.objects.only('equips').get(id=self.char_id)
        self.assertEqual(len(char.equips), 1 + self.original_equip_amount)
        
        app_test_helper._mongo_teardown_func()
        
    
    def test_not_enough_gold(self):
        self._prepare_equip()
        _id = self.equip_ids[0]
        cost_ids = self.equip_ids[1:]
        self._strength(_id, cost_ids, 10)
    
    def test_none_exists_strength(self):
        self._prepare_equip()
        _id = self.equip_ids[0]
        cost_ids = self.equip_ids[1:]
        cost_ids.append(9999)
        self._strength(_id, cost_ids, 2)
        
        char = MongoChar.objects.only('equips').get(id=self.char_id)
        self.assertEqual(len(char.equips), 3 + self.original_equip_amount)
        
        app_test_helper._mongo_teardown_func()
        




class SellEquipmentTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1,'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))
        
        c = MongoChar.objects.only('equips').get(id=self.char_id)
        self.original_equip_amount = len(c.equips)
        
    def tearDown(self):
        app_test_helper._teardown()

    def _prepare_equip(self):
        self.equip_ids = []
        for i in range(3):
            e = generate_and_save_equip(1, 1, self.char_id)
            self.equip_ids.append(int(e.id))
        
    
    def _sell(self, ids, ret=0):
        req = protomsg.SellEquipRequest()
        req.session = self.session
        req.ids.extend(ids)
        
        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/equip/sell/', data)
        msgs = app_test_helper.unpack_data(res)
        
        for id_of_msg, _, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["SellEquipResponse"]:
                data = protomsg.SellEquipResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def test_normal_sell(self):
        self._prepare_equip()
        self._sell(self.equip_ids)
        
        char = MongoChar.objects.only('equips').get(id=self.char_id)
        self.assertEqual(len(char.equips), 0 + self.original_equip_amount)
        
        app_test_helper._mongo_teardown_func()
        
    
    def test_none_exists_strength(self):
        self._sell([999], 2)
        
        app_test_helper._mongo_teardown_func()
        


class EmbedGemTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))
        
        e = generate_and_save_equip(1, 99, self.char_id)
        self.equip_id = int(e.id)
        
        gems = [(1, 10), (2, 1)]
        save_gem(gems, self.char_id)
        
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
