"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, TransactionTestCase

from protomsg import (
        RESPONSE_NOTIFY_TYPE,
        StartGameRequest,
        StartGameResponse,
        RegisterRequest,
        RegisterResponse,
        )
from utils import app_test_helper as tests
from models import User


class RegisterTest(TransactionTestCase):
    fixtures = ['server_list.json']
    
    def setUp(self):
        User.objects.create(
                email = '123@456.com',
                passwd = '123456'
                )
        User.objects.create(
                email = 'aaa@bbb.ccc',
                passwd = '123456',
                device_token = '123456'
                )

    def _register(self, email, password, device_token, ret):
        req = RegisterRequest()
        req.session = ""
        req.email = email
        req.password = password
        req.device_token = device_token
        
        data =  tests.pack_data(req)
        res = tests.make_request('/player/register/', data)

        num_of_msgs, id_of_msg, len_of_msg, msg = tests.unpack_data(res)

        self.assertEqual(num_of_msgs, 1)
        self.assertEqual(id_of_msg, RESPONSE_NOTIFY_TYPE["RegisterResponse"])
        self.assertEqual(len_of_msg, len(msg))

        data = RegisterResponse()
        data.ParseFromString(msg)
        self.assertEqual(data.ret, ret)

    def test_normal_register(self):
        self._register("000@00.000", "123456", "abcd", 0)

    def test_register_with_already_registed(self):
        self._register("aaa@bbb.ccc", "123456", "123456", 100)

    def test_register_with_already_bind(self):
        self._register("aaa@aaa.aaa", "123456", "123456", 0)

    def test_register_with_email_has_been_taken(self):
        self._register("123@456.com", "123456", "0987654321", 100)



class LoginTest(TransactionTestCase):
    def setUp(self):
        User.objects.create(
                email = '123@456.com',
                passwd = '123456'
                )

    def test_anonymous_login(self):
        req = StartGameRequest()
        req.session = ""
        req.anonymous.device_token = '1234567890'
        req.server_id = 1

        data = tests.pack_data(req)
        res = tests.make_request('/player/login/', data)

        num_of_msgs, id_of_msg, len_of_msg, msg = tests.unpack_data(res)

        self.assertEqual(num_of_msgs, 1)
        self.assertEqual(id_of_msg, RESPONSE_NOTIFY_TYPE["StartGameResponse"])
        self.assertEqual(len_of_msg, len(msg))

        data = StartGameResponse()
        data.ParseFromString(msg)
        self.assertEqual(data.ret, 0)

    def _regular_login(self, email, password, ret):
        req = StartGameRequest()
        req.session = ""
        req.regular.email = email
        req.regular.password = password
        req.server_id = 1

        data = tests.pack_data(req)
        res = tests.make_request('/player/login/', data)

        num_of_msgs, id_of_msg, len_of_msg, msg = tests.unpack_data(res)

        self.assertEqual(num_of_msgs, 1)
        self.assertEqual(id_of_msg, RESPONSE_NOTIFY_TYPE["StartGameResponse"])
        self.assertEqual(len_of_msg, len(msg))

        data = StartGameResponse()
        data.ParseFromString(msg)
        self.assertEqual(data.ret, ret)


    def test_regular_login_with_non_exists(self):
        self._regular_login('aaa@bbb.ccc', '123456', 151)

    def test_regular_login_with_exists(self):
        self._regular_login('123@456.com', '123456', 0)

    def test_regular_login_with_wrong_password(self):
        self._regular_login('123@456.com', 'abcd', 150)

