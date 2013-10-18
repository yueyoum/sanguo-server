"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import urllib2
import struct

FMT = struct.Struct('>i')

from django.test import TestCase
from django_nose import FastFixtureTestCase

from msg import (
        RESPONSE_NOTIFY_TYPE,
        GetServerListRequest,
        GetServerListResponse,
        )

from utils import tests

class ServerListTest(FastFixtureTestCase):
    fixtures = ['server_list.json',]

    def test_get_server_list(self):
        req = GetServerListRequest()
        req.anonymous.device_token = '111111'

        data = tests.pack_data(req)
        res = tests.make_request('/world/server-list/', data)
        num_of_msgs, id_of_msg, len_of_msg, msg = tests.unpack_data(res)

        self.assertEqual(num_of_msgs, 1)
        self.assertEqual(id_of_msg, RESPONSE_NOTIFY_TYPE["GetServerListResponse"])
        self.assertEqual(len_of_msg, len(msg))

        data = GetServerListResponse()
        data.ParseFromString(msg)
        self.assertEqual(data.ret, 0)
        self.assertTrue(len(data.servers) >= 1)

