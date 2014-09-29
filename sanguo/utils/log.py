# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/28/14'

import json
import struct
import logging

# import zmq
# import msgpack

import arrow
from django.conf import settings


# fmt = struct.Struct('>i')
# LOG_SYSTEM_ID = fmt.pack(1)
# LOG_RESOURCE_ID = fmt.pack(2)
#
# context = zmq.Context()
# sock = context.socket(zmq.PUSH)
#
# sock.connect("tcp://{0}:{1}".format(settings.LOG_MAN_HOST, settings.LOG_MAN_PORT))

logger = logging.getLogger('sanguo')

TIME_ZONE = settings.TIME_ZONE

class LogManHandler(logging.Handler):
    def emit(self, record):
        pass
        # if record.log_type_id == 1:
        #     data = _make_system_data(record)
        # elif record.log_type_id == 2:
        #     data = _make_resource_data(record)
        # else:
        #     print "NOT SUPPORTED LOG TYPE ID", record.log_type_id
        #     return

        # sock.send(data)


# def _make_system_data(record):
#     data = {
#         'levelname': record.levelname,
#         'error_id': record.error_id,
#         'char_id': record.char_id,
#         'func_name': record.func_name,
#         'msg': record.error_msg,
#         'occurred_at': record.occurred_at,
#     }
#
#     binary = msgpack.packb(data)
#     return '%s%s' % (LOG_SYSTEM_ID, binary)
#
# def _make_resource_data(record):
#     data = {
#         'char_id': record.char_id,
#         'income': record.income,
#         'func_name': record.func_name,
#         'exp': record.exp,
#         'official_exp': record.official_exp,
#         'gold': record.gold,
#         'sycee': record.sycee,
#         'heros': json.dumps(record.heros),
#         'souls': json.dumps(record.souls),
#         'equipments': json.dumps(record.equipments),
#         'gems': json.dumps(record.gems),
#         'stuffs': json.dumps(record.stuffs),
#         'des': record.des,
#         'occurred_at': record.occurred_at,
#     }
#
#     binary = msgpack.packb(data)
#     return '%s%s' % (LOG_RESOURCE_ID, binary)


def system_logger(error_id, char_id, func_name, error_msg):
    extra = {
        'log_type_id': 1,
        'error_id': error_id,
        'char_id': char_id,
        'func_name': func_name,
        'error_msg': error_msg,
        'occurred_at': arrow.utcnow().to(TIME_ZONE).format('YYYY-MM-DD HH:mm:ss'),
    }

    logger.debug("Error_id: {0}. Char_id: {1}. Func_name: {2}. Msg: {3}".format(
                error_id, char_id, func_name, error_msg.encode('utf-8')),
                extra=extra
                )
