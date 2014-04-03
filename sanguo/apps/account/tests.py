"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from protomsg import (
    RESPONSE_NOTIFY_TYPE,
    StartGameRequest,
    StartGameResponse,
    RegisterRequest,
    RegisterResponse,
    )
from utils import app_test_helper as tests
from models import Account


def teardown():
    tests._teardown()


def account_create(email, password, token):
    req = RegisterRequest()
    req.session = ""
    req.email = email
    req.password = password
    req.device_token = token

    data = tests.pack_data(req)
    res = tests.make_request('/player/register/', data)
    return res

class RegisterTest(TestCase):
    def teardown(self):
        tests._teardown()


    def _register(self, email, password, device_token, ret):
        res = account_create(email, password, device_token)


        msgs = tests.unpack_data(res)
        id_of_msg, len_of_msg, msg = msgs[0]

        self.assertEqual(len(msgs), 1)
        self.assertEqual(id_of_msg, RESPONSE_NOTIFY_TYPE["RegisterResponse"])
        self.assertEqual(len_of_msg, len(msg))

        data = RegisterResponse()
        data.ParseFromString(msg)
        self.assertEqual(data.ret, ret)

    def test_normal_register(self):
        self._register("000@00.000", "123456", "abcd", 0)

    def test_register_bind(self):
        self._register("aaa@aaa.aaa", "123456", "123456", 0)

    def test_register_with_email_has_been_taken(self):
        self._register("www@bbb.com", "123456", "0987654321", 0)
        self._register("www@bbb.com", "123456", "0987654321", 100)


class LoginTest(TestCase):
    def teardown(self):
        tests._teardown()


    def test_anonymous_login(self):
        req = StartGameRequest()
        req.session = ""
        req.anonymous.device_token = '123456'
        req.server_id = 1

        data = tests.pack_data(req)
        res = tests.make_request('/player/login/', data)

        msgs = tests.unpack_data(res)

    def _regular_login(self, email, password, ret):
        req = StartGameRequest()
        req.session = ""
        req.regular.email = email
        req.regular.password = password
        req.server_id = 1

        data = tests.pack_data(req)
        res = tests.make_request('/player/login/', data)

        msgs = tests.unpack_data(res)

        for id_of_msg, len_of_msg, msg in msgs:
            if id_of_msg == RESPONSE_NOTIFY_TYPE["StartGameResponse"]:
                data = StartGameResponse()
                data.ParseFromString(msg)
                self.assertEqual(data.ret, ret)


    def test_regular_login_with_non_exists(self):
        self._regular_login('123456', '123456', 121)

    def test_regular_login_with_exists(self):
        account_create('123@456.com', '12345', 'xxx')
        self._regular_login('123@456.com', '12345', 0)

    def test_regular_login_with_wrong_password(self):
        account_create('aaa@bbb.com', '12345', 'xxx')
        self._regular_login('aaa@bbb.com', 'abcd', 120)

    def test_regular_login_ok(self):
        account_create('xxx@xxx.xxx', '12345', 'xxx')
        self._regular_login('xxx@xxx.xxx', '12345', 0)

