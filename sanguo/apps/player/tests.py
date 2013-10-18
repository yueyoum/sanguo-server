"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django_nose import FastFixtureTestCase

from msg import (
        RESPONSE_NOTIFY_TYPE,
        StartGameRequest,
        StartGameResponse,
        RegisterRequest,
        RegisterResponse,
        )
from utils import tests


class RegisterTest(FastFixtureTestCase):
    fixtures = ['server_list.json']

    def test_register(self):
        req = RegisterRequest()
        req.email = 'aaa@bbb.ccc'
        req.password = '1111111'
        req.device_token = '1234567890'
        
        data =  tests.pack_data(req)
        res = tests.make_request('/player/register/', data)

        num_of_msgs, id_of_msg, len_of_msg, msg = tests.unpack_data(res)

        self.assertEqual(num_of_msgs, 1)
        self.assertEqual(id_of_msg, RESPONSE_NOTIFY_TYPE["RegisterResponse"])
        self.assertEqual(len_of_msg, len(msg))

        data = RegisterResponse()
        data.ParseFromString(msg)
        # self.assertEqual(data.ret, 0)


class LoginTest(TestCase):
    def test_anonymous_login(self):
        req = StartGameRequest()
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


    def test_regular_login(self):
        req = StartGameRequest()
        req.regular.email = '123@456.com'
        req.regular.password = '1234567890'
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
