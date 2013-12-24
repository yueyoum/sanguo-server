"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, TransactionTestCase
import protomsg

from core.character import char_initialize
from utils import crypto
from utils import app_test_helper as tests


def teardown():
    tests._teardown()


class CmdTest(TransactionTestCase):
    def setUp(self):
        char = char_initialize(1, 1, 'a')
        self.session = crypto.encrypt('1:1:{0}'.format(char.id))
    
    def tearDown(self):
        tests._teardown()
    
    def _cmd(self, action, tp, param):
        req = protomsg.TestRequest()
        req.session = self.session
        req.action = action
        req.tp = tp
        req.param = param
        
        data = tests.pack_data(req)
        res = tests.make_request('/test/', data)
        msgs = tests.unpack_data(res)
    
    def test_add_hero(self):
        self._cmd(1, 7, 10)
    
    def test_add_exp(self):
        self._cmd(1, 1, 1000)
    
    def test_add_equip(self):
        self._cmd(1, 5, 1)
    
    def test_add_gem(self):
        self._cmd(1, 6, 1)



