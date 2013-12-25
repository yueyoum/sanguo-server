from django.test import TransactionTestCase
import protomsg
from protomsg import RESPONSE_NOTIFY_TYPE
from core import GLOBAL
from core.character import char_initialize
from utils import crypto
from utils import app_test_helper as tests



class PVETest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        
    def tearDown(self):
        tests._teardown()

    def _pve(self, stage_id):
        req = protomsg.PVERequest()
        req.session = self.session
        req.stage_id = stage_id

        data = tests.pack_data(req)
        res = tests.make_request('/pve/', data)
        msgs = tests.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["PVEResponse"]:
                data = protomsg.PVEResponse()
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
                self.assertEqual(data.ret, 2)
        
    



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
        
        data = tests.pack_data(req)
        res = tests.make_request('/plunder/', data)
        msgs = tests.unpack_data(res)
