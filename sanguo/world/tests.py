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
        GetServerListRequest,
        GetServerListResponse,
        )


class ServerListTest(TestCase):
    # fixtures = ['server_list.json',]

    def test_get_server_list(self):
        req = GetServerListRequest()
        req.anonymous.device_token = '111111'

        id_of_msg = REQUEST_TYPE_REV[req.DESCRIPTOR.name]
        data = FMT.pack(id_of_msg) + req.SerializeToString()
        
        url = 'http://127.0.0.1:8000/world/server-list/'
        req = urllib2.Request(url, data=data)
        response = urllib2.urlopen(req)

        res = response.read()

        num_of_msgs = FMT.unpack(res[:4])
        self.assertEqual(num_of_msgs[0], 1)
        res = res[4:]
        id_of_msg = FMT.unpack(res[:4])
        self.assertEqual(id_of_msg[0], RESPONSE_NOTIFY_TYPE["GetServerListResponse"])
        res = res[4:]
        len_of_msg = FMT.unpack(res[:4])
        res = res[4:]
        self.assertEqual(len(res), len_of_msg[0])

        data = GetServerListResponse()
        data.ParseFromString(res)
        self.assertEqual(data.ret, 0)
        self.assertTrue(len(data.servers) >= 1)

