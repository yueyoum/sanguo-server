from django.test import TransactionTestCase

import protomsg
from protomsg import RESPONSE_NOTIFY_TYPE
from core.character import char_initialize
from utils import app_test_helper
from utils import crypto
from core.character import Char
from core.equip import generate_and_save_equip



class SocketTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.char_id = char.id
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        e = generate_and_save_equip(1, 1, char.id)
        self.e = e
        self.equip_id = e.id
        
    def tearDown(self):
        app_test_helper._teardown()

    def _set_socket(self, hero_id, weapon_id, armor_id, jewelry_id, ret):
        req = protomsg.SetSocketRequest()
        req.session = self.session
        req.socket.id = 1
        req.socket.hero_id = hero_id
        req.socket.weapon_id = weapon_id
        req.socket.armor_id = armor_id
        req.socket.jewelry_id = jewelry_id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/socket/set/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["SetSocketResponse"]:
                data = protomsg.SetSocketResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def test_normal(self):
        char = Char(self.char_id)
        hero = char.save_hero(1)
        hero_id = hero[0]
        self._set_socket(hero_id, self.equip_id, 0, 0, 0)
    
    def test_error_tp(self):
        char = Char(self.char_id)
        hero = char.save_hero(1)
        hero_id = hero[0]
        
        if self.e.tp == 1:
            args = [hero_id, 0, 0, self.e.id, 402]
        elif self.e.tp == 2:
            args = [hero_id, 0, self.e.id, 0, 402]
        else:
            args = [hero_id, self.e.id, 0, 0, 402]
        
        self._set_socket(*args)
        
    
    def test_none_exists(self):
        self._set_socket(99999, 0, 0, 0, 2)
    
        


class FormationTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
        self.socket_ids = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        
    def tearDown(self):
        app_test_helper._teardown()

    def _set_formation(self, socket_ids, ret=0):
        req = protomsg.SetFormationRequest()
        req.session = self.session
        req.socket_ids.extend(socket_ids)

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/formation/set/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["SetFormationResponse"]:
                data = protomsg.SetFormationResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)


    def test_set_formation(self):
        self._set_formation([1, 0, 0, 3, 0, 0, 2, 0, 0])
    
    def test_error_set(self):
        self._set_formation([1, 0, 0, 3, 0, 0, 0, 0, 99], 2)
        self._set_formation([1, 0, 0, 3, 0, 0, 2, 0], 400)
        self._set_formation([1, 0, 3, 0, 0, 0, 2, 0, 0], 403)


