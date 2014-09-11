# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/8/14'

import struct

from protomsg import RESPONSE_NOTIFY_TYPE


NUM_FIELD = struct.Struct('>i')
METHOD_POST = 'POST'
MSG_TYPE_TO_HUB= {102, 105, 4200, 4202}
MSG_TYPE_EMPTY_SESSION = {100, 102, 105, 4200, 4202}
MSG_TYPE_VERSION_CHECKER = 51
MSG_TYPE_START_GAME = 100

# 最大消息个数，超过就直接返回403
MAX_NUM_FIELD_AMOUNT = 10

def unpack_msg(res):
    msg_id = NUM_FIELD.unpack(res[:4])[0]
    res = res[4:]
    len_of_msg = NUM_FIELD.unpack(res[:4])[0]
    res = res[4:]
    return msg_id, res[:len_of_msg], res[len_of_msg:]


def pack_msg(msg, session=""):
    msg.session = session
    binary = msg.SerializeToString()
    id_of_msg = RESPONSE_NOTIFY_TYPE[msg.DESCRIPTOR.name]
    len_of_msg = len(binary)

    data = '%s%s%s' % (
        NUM_FIELD.pack(id_of_msg),
        NUM_FIELD.pack(len_of_msg),
        binary
    )

    return data

