from django.test import TransactionTestCase
import protomsg
from protomsg import RESPONSE_NOTIFY_TYPE

from core.character import char_initialize
from utils import crypto, app_test_helper as tests
from protomsg import Prisoner as PrisonProtoMsg
from core.mongoscheme import MongoPrison, MongoHero
from core.prison import save_prisoner, Prison
from core.character import Char


class OpenSlotTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
    
    def tearDown(self):
        tests._teardown()
    
    def _open(self, ret=0):
        req = protomsg.OpenTrainSlotRequest()
        req.session = self.session
        
        data = tests.pack_data(req)
        res = tests.make_request('/prison/open/', data)
        msgs = tests.unpack_data(res)
        
        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["OpenTrainSlotResponse"]:
                d = protomsg.OpenTrainSlotResponse()
                d.ParseFromString(msg)
                self.assertEqual(d.ret, ret)
    
    def test_not_enough_sycee(self):
        self._open(11)
    
    def test_all_opened(self):
        p = Prison(self.char_id)
        p.p.amount = p.max_slots
        p.p.save()
        
        self._open(804)
    
    def test_normal_open(self):
        p = Prison(self.char_id)
        sycee = p.open_slot_cost
        c = Char(self.char_id)
        c.update(sycee=sycee)
        
        cache_char = c.cacheobj
        self.assertEqual(cache_char.sycee, sycee)
        
        self._open()
        
        cache_char = c.cacheobj
        self.assertEqual(cache_char.sycee, 0)
        


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
        ps = MongoPrison.objects.get(id=self.char_id)
        ps.prisoners[str(pid)].status = st
        ps.save()
    
    def test_normal_train(self):
        self._train(self.p1.id)
    
    def test_none_exist_train(self):
        self._train(9999, ret=2)
    
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
        
        ps = MongoPrison.objects.get(id=self.char_id)
        self.assertTrue(str(self.p1.id) not in ps.prisoners.keys())
        
        heros = MongoHero.objects(char=self.char_id)
        hoids = [h.oid for h in heros]
        self.assertTrue(self.p1.oid in hoids)
    
    
    def test_error_get(self):
        self._change_status(self.p2.id, PrisonProtoMsg.IN)
        self._get(self.p2.id, ret=803)