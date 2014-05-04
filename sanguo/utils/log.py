# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/28/14'


import logging

import zmq
import msgpack

from django.conf import settings


context = zmq.Context()
sock = context.socket(zmq.PUSH)

sock.connect("tcp://{0}:{1}".format(settings.LOG_MAN_HOST, settings.LOG_MAN_PORT))


class LogManHandler(logging.Handler):
    def emit(self, record):
        data = {
            'levelname': record.levelname,
            'node_id': record.node_id,
            'error_id': record.error_id,
            'char_id': record.char_id,
            'func_name': record.func_name,
            'msg': record.error_msg,
            'occurred_at': record.occurred_at,
        }

        binary = msgpack.packb(data)
        sock.send(binary)
