"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, TransactionTestCase
import protomsg


from protomsg import (
        RESPONSE_NOTIFY_TYPE,
        PVERequest,
        PVEResponse,
        )
from core import GLOBAL
from core.character import char_initialize
from core.gem import save_gem
from core.equip import generate_and_save_equip
from utils import crypto
from utils import app_test_helper as tests

from core.prison import save_prisoner
from core.mongoscheme import Prison, MongoHero
from protomsg import Prisoner as PrisonProtoMsg

def teardown():
    tests._teardown()


class CmdTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
    
    def tearDown(self):
        tests._teardown()
    
    def _cmd(self, action, tp, param):
        req = protomsg.TestRequest()
        req.session = self.session
        req.action = action
        req.tp = tp
        req.param = param
        
        data = tests.pack_data(req)
        res = tests.make_request('/test/', data)
        msgs = tests.unpack_data(res)
    
    def test_add_hero(self):
        self._cmd(1, 7, 10)
    
    def test_add_exp(self):
        self._cmd(1, 1, 1000)
    
    def test_add_equip(self):
        self._cmd(1, 5, 1)
    
    def test_add_gem(self):
        self._cmd(1, 6, 1)



class BattleTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        
    def tearDown(self):
        tests._teardown()

    def _pve(self, stage_id):
        req = PVERequest()
        req.session = self.session
        req.stage_id = stage_id

        data = tests.pack_data(req)
        res = tests.make_request('/pve/', data)
        msgs = tests.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["PVEResponse"]:
                data = PVEResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.stage_id, stage_id)
    
    def test_pve(self):
        #stages = GLOBAL.STAGE
        #for sid in stages.keys():
        #    self._pve(sid)
        self._pve(1)


class PVPTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        
        char = char_initialize(2, 1, 'b')
        self.other_char_id = char.id
        
    def tearDown(self):
        tests._teardown()


    def test_pvp(self):
        req = protomsg.ArenaRequest()
        req.session = self.session
        
        data = tests.pack_data(req)
        res = tests.make_request('/pvp/', data)
        msgs = tests.unpack_data(res)


class SocketTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        generate_and_save_equip(1, 1, char.id)
        
    def tearDown(self):
        tests._teardown()

    def test_set_socket(self):
        req = protomsg.SetSocketRequest()
        req.session = self.session
        req.socket.id = 1
        req.socket.hero_id = 1
        req.socket.weapon_id = 1
        req.socket.armor_id = 0
        req.socket.jewelry_id = 0

        data = tests.pack_data(req)
        res = tests.make_request('/socket/set/', data)
        msgs = tests.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["SetSocketResponse"]:
                data = protomsg.SetSocketResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, 0)
                self.assertEqual(data.socket.id, 1)
                self.assertEqual(data.socket.hero_id, 1)



class GemTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        gems = (
            (49, 4),
        )
        save_gem(gems, char.id)
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
    
    def tearDown(self):
        tests._teardown()
    
    
    def _merge(self, _id, _amount, using_sycee, ret=0):
        req = protomsg.MergeGemRequest()
        req.session = self.session
        req.id = _id
        req.amount = _amount
        req.using_sycee = using_sycee
        
        
        data = tests.pack_data(req)
        res = tests.make_request('/gem/merge/', data)
        msgs = tests.unpack_data(res)
        
        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["MergeGemResponse"]:
                data = protomsg.MergeGemResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)
        
    
    def test_normal_merge(self):
        self._merge(50, 1, False)
    
    def test_error_merge(self):
        self._merge(49, 1, False, ret=600)




class HangTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
    
    def tearDown(self):
        tests._teardown()
    
    
    def _hang(self):
        req = protomsg.HangRequest()
        req.session = self.session
        req.stage_id = 1
        req.hours = 8
        
        data = tests.pack_data(req)
        res = tests.make_request('/hang/', data)
        msgs = tests.unpack_data(res)
    
        return msgs
    
    def _cancel(self):
        req = protomsg.HangCancelRequest()
        req.session = self.session
        
        data = tests.pack_data(req)
        res = tests.make_request('/hang/cancel/', data)
        msgs = tests.unpack_data(res)
        
        return msgs
        
    
    
    def test_normal_hang(self):
        msgs = self._hang()
        
        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["HangResponse"]:
                data = protomsg.HangResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, 0)
        
        msgs = self._cancel()
        
        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["HangCancelResponse"]:
                data = protomsg.HangCancelResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, 0)
        
        
    
    def test_error_hang_cancel(self):
        msgs = self._cancel()
        
        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["HangCancelResponse"]:
                data = protomsg.HangCancelResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, 702)
        
    

class PrizeTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
    
    def tearDown(self):
        tests._teardown()
    
    
    def _prize_get(self, pid):
        req = protomsg.PrizeRequest()
        req.session = self.session
        req.prize_id = pid
    
        data = tests.pack_data(req)
        res = tests.make_request('/prize/', data)
        msgs = tests.unpack_data(res)
    
        return msgs

    
    def test_error_prize(self):
        msgs = self._prize_get(1)
    
    
    def test_normal_prize(self):
        from core.mongoscheme import Hang
        h = Hang(
            id = self.char_id,
            stage_id = 1,
            hours = 8,
            start = 100,
            finished = True,
            actual_hours = 8
        )
        
        h.save()
        
        msgs = self._prize_get(1)
    

class PlunderTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        
        other_char = char_initialize(2, 1, 'b')
        self.other_char_id = other_char.id
    
    def tearDown(self):
        tests._teardown()

    def test_plunder_list(self):
        req = protomsg.PlunderListRequest()
        req.session = self.session
        
        data = tests.pack_data(req)
        res = tests.make_request('/plunder/list/', data)
        msgs = tests.unpack_data(res)
        
    def test_plunder_battle(self):
        req = protomsg.PlunderRequest()
        req.session = self.session
        req.id = self.other_char_id
        req.npc = False
        
        data = tests.pack_data(req)
        res = tests.make_request('/plunder/', data)
        msgs = tests.unpack_data(res)
        

class PrisonTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        
        self.p1 = save_prisoner(self.char_id, 1)
        
        self.p2 = save_prisoner(self.char_id, 2)
        
    def tearDown(self):
        tests._teardown()

    def _train(self, hero_id, ret=0):
        req = protomsg.TrainRequest()
        req.session = self.session
        req.hero = hero_id

        data = tests.pack_data(req)
        res = tests.make_request('/prisoner/train/', data)
        msgs = tests.unpack_data(res)
        
        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["TrainResponse"]:
                d = protomsg.TrainResponse()
                d.ParseFromString(msg)
                self.assertEqual(d.ret, ret)
    
    def _change_status(self, pid, st):
        ps = Prison.objects.get(id=self.char_id)
        ps.prisoners[str(pid)].status = st
        ps.save()
    
    def test_normal_train(self):
        self._train(self.p1.id)
    
    def test_none_exist_train(self):
        self._train(9999, ret=800)
    
    def test_error_train(self):
        self._change_status(self.p2.id, PrisonProtoMsg.IN)
        self._train(self.p2.id, ret=801)
    
    
    def _get(self, hero_id, ret=0):
        req = protomsg.GetPrisonerRequest()
        req.session = self.session
        req.hero = hero_id
        
        data = tests.pack_data(req)
        res = tests.make_request('/prisoner/get/', data)
        msgs = tests.unpack_data(res)
        
        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["GetPrisonerResponse"]:
                d = protomsg.TrainResponse()
                d.ParseFromString(msg)
                self.assertEqual(d.ret, ret)
        
    def test_normal_get(self):
        self._change_status(self.p1.id, PrisonProtoMsg.FINISH)
        self._get(self.p1.id)
        
        ps = Prison.objects.get(id=self.char_id)
        self.assertTrue(str(self.p1.id) not in ps.prisoners.keys())
        
        heros = MongoHero.objects(char=self.char_id)
        hoids = [h.oid for h in heros]
        self.assertTrue(self.p1.oid in hoids)
    
    
    def test_error_get(self):
        self._change_status(self.p2.id, PrisonProtoMsg.IN)
        self._get(self.p2.id, ret=803)
