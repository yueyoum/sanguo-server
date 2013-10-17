"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import urllib2
import struct

FMT = struct.Struct('>i')

from django.test import TestCase

from msg import (
        RESPONSE_NOTIFY_TYPE,
        REQUEST_TYPE_REV,
        StartGameRequest,
        StartGameResponse,
        RegisterRequest,
        RegisterResponse,
        )

class RegisterTest(TestCase):
    def test_register(self):
        req = RegisterRequest()
        req.email = 'aaa@bbb.ccc'
        req.password = '1111111'
        req.device_token = '1234567890'

        id_of_msg = REQUEST_TYPE_REV[req.DESCRIPTOR.name]
        data = FMT.pack(id_of_msg) + req.SerializeToString()

        url = 'http://127.0.0.1:8000/player/register/'
        req = urllib2.Request(url, data=data)
        response = urllib2.urlopen(req)

        res = response.read()

        num_of_msgs = FMT.unpack(res[:4])
        self.assertEqual(num_of_msgs[0], 1)
        res = res[4:]
        id_of_msg = FMT.unpack(res[:4])
        self.assertEqual(id_of_msg[0], RESPONSE_NOTIFY_TYPE["RegisterResponse"])
        res = res[4:]
        len_of_msg = FMT.unpack(res[:4])
        res = res[4:]
        self.assertEqual(len(res), len_of_msg[0])

        data = RegisterResponse()
        data.ParseFromString(res)
        self.assertEqual(data.ret, 0)


class LoginTest(TestCase):
    def test_anonymous_login(self):
        req = StartGameRequest()
        req.anonymous.device_token = '1234567890'
        req.server_id = 1
        data = req.SerializeToString()

        id_of_msg = REQUEST_TYPE_REV[req.DESCRIPTOR.name]
        data = FMT.pack(id_of_msg) + data

        url = 'http://127.0.0.1:8000/player/login/'
        req = urllib2.Request(url, data=data)
        response = urllib2.urlopen(req)

        res = response.read()
        
        num_of_msgs = FMT.unpack(res[:4])
        self.assertEqual(num_of_msgs[0], 1)
        res = res[4:]
        id_of_msg = FMT.unpack(res[:4])
        self.assertEqual(id_of_msg[0], RESPONSE_NOTIFY_TYPE["StartGameResponse"])
        res = res[4:]
        len_of_msg = FMT.unpack(res[:4])
        res = res[4:]
        self.assertEqual(len(res), len_of_msg[0])

        data = StartGameResponse()
        data.ParseFromString(res)
        self.assertEqual(data.ret, 0)


    def test_regular_login(self):
        req = StartGameRequest()
        req.regular.email = '123@456.com'
        req.regular.password = '1234567890'
        req.server_id = 1
        data = req.SerializeToString()

        id_of_msg = REQUEST_TYPE_REV[req.DESCRIPTOR.name]
        data = FMT.pack(id_of_msg) + data

        url = 'http://127.0.0.1:8000/player/login/'
        req = urllib2.Request(url, data=data)
        response = urllib2.urlopen(req)
        
        res = response.read()
        
        num_of_msgs = FMT.unpack(res[:4])
        self.assertEqual(num_of_msgs[0], 1)
        res = res[4:]
        id_of_msg = FMT.unpack(res[:4])
        self.assertEqual(id_of_msg[0], RESPONSE_NOTIFY_TYPE["StartGameResponse"])
        res = res[4:]
        len_of_msg = FMT.unpack(res[:4])
        res = res[4:]
        self.assertEqual(len(res), len_of_msg[0])

        data = StartGameResponse()
        data.ParseFromString(res)
        self.assertEqual(data.ret, 0)

