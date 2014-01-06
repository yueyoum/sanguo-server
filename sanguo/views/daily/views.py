# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/6/14'

from core.daily import CheckIn
from utils.decorate import message_response


@message_response("CheckInResponse")
def checkin(request):
    c = CheckIn(request._char_id)
    c.checkin()
    return None


@message_response("GetCheckInRewardResponse")
def get_checkin_reward(request):
    c = CheckIn(request._char_id)
    c.get_reward(request._proto.tp)
    return None