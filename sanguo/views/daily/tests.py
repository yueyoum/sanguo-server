# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

from core.daily import CheckIn
from core.exception import InvalidOperate

from utils import app_test_helper

teardown = app_test_helper._teardown


def test_checkin():
    c = CheckIn(1)
    assert c.whole_days == 0

    c.checkin()
    assert c.whole_days == 1

    app_test_helper._teardown()

def test_get_checkin_reward():
    c = CheckIn(1)
    c.get_reward(2)
    try:
        c.get_reward(2)
    except InvalidOperate:
        pass

    app_test_helper._teardown()
