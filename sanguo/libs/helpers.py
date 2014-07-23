# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-7-23'


def make_account_dict_from_message(msg):
    # msg is message Login which is defined in account.proto
    if msg.tp == 1:
        return {
            'method': 'anonymous',
            'token': int(msg.anonymous.device_token),
        }
    if msg.tp == 2:
        if not msg.regular.email or not msg.regular.password:
            raise Exception("regular.email and regular.password can not empty. email = {0}, password = {1}".format(
                msg.regular.email, msg.regular.password,
            ))
        return {
            'method': 'regular',
            'name': msg.regular.email,
            'password': msg.regular.password,
        }
    if msg.tp == 3:
        if not msg.third.platform or not msg.third.uid:
            raise Exception("third.platform and third.uid can not be empty. platform = {0}, uid = {1}".format(
                msg.third.platform, msg.third.uid
            ))
        return {
            'method': 'third',
            'platform': msg.third.platform,
            'uid': msg.third.uid,
            'param': msg.third.param,
        }

    raise Exception("Login message, Unsupported tp: {0}".format(msg.tp))
