# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '12/31/13'

from django.test import TestCase


from core.friend import Friend
from core.character import char_initialize
from utils import app_test_helper
from utils import crypto

import protomsg
from protomsg import RESPONSE_NOTIFY_TYPE

class FriendTest(TestCase):
    def setUp(self):
        char_initialize(1, 1, 1, 'a')
        self.char_id = 1
        self.session = crypto.encrypt('1:1:{0}'.format(self.char_id))

        char_initialize(2, 1, 2, 'b')
        self.char_two_id = 2
        self.char_two_session = crypto.encrypt('1:1:{0}'.format(self.char_two_id))

    def tearDown(self):
        app_test_helper._teardown()


    def test_player_list(self):
        req = protomsg.PlayerListRequest()
        req.session = self.session
        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/friend/player-list/', data)
        msgs = app_test_helper.unpack_data(res)



    def _add(self, _id=None, name=None, ret=0, session=None):
        if not session:
            session = self.session
        req = protomsg.FriendAddRequest()
        req.session = session
        if _id:
            req.id = _id
        else:
            req.name = name

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/friend/add/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, _, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE['FriendAddResponse']:
                data = protomsg.FriendAddResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def _terminate(self, _id, ret=0, session=None):
        if not session:
            session = self.session
        req = protomsg.FriendTerminateRequest()
        req.session = session
        req.id = _id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/friend/terminate/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, _, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE['FriendTerminateResponse']:
                data = protomsg.FriendTerminateResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)


    def _cancel(self, _id, ret=0, session=None):
        if not session:
            session = self.session
        req = protomsg.FriendCancelRequest()
        req.session = session
        req.id = _id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/friend/cancel/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, _, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE['FriendCancelResponse']:
                data = protomsg.FriendCancelResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)


    def _accept(self, _id, ret=0, session=None):
        if not session:
            session = self.session
        req = protomsg.FriendAcceptRequest()
        req.session = session
        req.id = _id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/friend/accept/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, _, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE['FriendAcceptResponse']:
                data = protomsg.FriendAcceptResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)

    def _refuse(self, _id, ret=0, session=None):
        if not session:
            session = self.session
        req = protomsg.FriendRefuseRequest()
        req.session = session
        req.id = _id

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request('/friend/refuse/', data)
        msgs = app_test_helper.unpack_data(res)

        for id_of_msg, _, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE['FriendRefuseResponse']:
                data = protomsg.FriendRefuseResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)


    def test_normal_add_id(self):
        self._add(self.char_two_id)

        f = Friend(self.char_id)
        self.assertTrue(str(self.char_two_id) in f.mf.friends)
        self.assertEqual(f.mf.friends[str(self.char_two_id)], protomsg.FRIEND_ACK)

        f = Friend(self.char_two_id)
        self.assertTrue(self.char_id in f.mf.accepting)

        app_test_helper._mongo_teardown_func()

    def test_error_add_id(self):
        self._add(_id=999, ret=2)

    def test_error_add_name(self):
        self._add(name='xxx', ret=3)

    def test_duplicate_add(self):
        self._add(self.char_two_id)
        self._add(self.char_two_id, ret=1000)

        app_test_helper._mongo_teardown_func()


    def test_normal_cancel(self):
        self._add(self.char_two_id)

        self._cancel(self.char_two_id)

        f = Friend(self.char_id)
        self.assertEqual(len(f.mf.friends), 0)
        f = Friend(self.char_two_id)
        self.assertEqual(len(f.mf.accepting), 0)
        app_test_helper._mongo_teardown_func()



    def test_error_accept(self):
        self._accept(999, 2)

    def test_normal_accept(self):
        self._add(self.char_two_id)
        self._accept(self.char_id, ret=0, session=self.char_two_session)

        f = Friend(self.char_id)
        self.assertTrue(str(self.char_two_id) in f.mf.friends)
        self.assertEqual(f.mf.friends[str(self.char_two_id)], protomsg.FRIEND_OK)

        f = Friend(self.char_two_id)
        self.assertTrue(str(self.char_id) in f.mf.friends)
        self.assertEqual(f.mf.friends[str(self.char_id)], protomsg.FRIEND_OK)

        app_test_helper._mongo_teardown_func()


    def test_normal_terminate(self):
        self._add(self.char_two_id)
        self._accept(self.char_id, session=self.char_two_session)
        self._terminate(self.char_two_id)

        f = Friend(self.char_id)
        self.assertEqual(len(f.mf.friends), 0)

        f = Friend(self.char_two_id)
        self.assertEqual(len(f.mf.friends), 0)

        app_test_helper._mongo_teardown_func()


    def test_norma_refuse(self):
        self._add(self.char_two_id)
        self._refuse(self.char_id, session=self.char_two_session)

        f = Friend(self.char_id)
        self.assertEqual(len(f.mf.friends), 0)

        f = Friend(self.char_two_id)
        self.assertEqual(len(f.mf.accepting), 0)
        self.assertEqual(len(f.mf.friends), 0)
        app_test_helper._mongo_teardown_func()

