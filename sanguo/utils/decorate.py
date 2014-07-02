import logging

import arrow
from django.http import HttpResponse
from django.conf import settings

from core.exception import SanguoException
from utils import cache
from utils import pack_msg
from utils.checkers import func_opened
import protomsg
from preset import errormsg

from libs.decorate import json_return

logger = logging.getLogger('sanguo')

TIME_ZONE = settings.TIME_ZONE

def message_response(message_name):
    def deco(func):
        def wrap(request, *args, **kwargs):
            m = getattr(protomsg, message_name)()
            m.ret = 0
            try:
                res = func(request, *args, **kwargs)
                if res is None:
                    return HttpResponse(pack_msg(m), content_type='text/plain')
                if isinstance(res, (list, tuple)):
                    msg_amount = len(res)
                    res = ''.join(res)
                    response = HttpResponse(res, content_type='text/plain')
                    response._msg_amount = msg_amount
                    return response
                return HttpResponse(res, content_type='text/plain')
            except SanguoException as e:
                m.ret = e.error_id
                return HttpResponse(pack_msg(m), content_type='text/plain')

        return wrap
    return deco


def operate_guard(func_name, interval, keep_result=False, char_id_name='_char_id'):
    def deco(func):
        def wrap(request, *args, **kwargs):
            char_id = getattr(request, char_id_name, None)
            if not char_id:
                return func(request, *args, **kwargs)

            redis_key = 'opt:{0}:{1}'.format(func_name, char_id)
            if keep_result:
                data = cache.get(redis_key)
                if data:
                    extra = {
                        'log_type_id': 1,
                        'error_id': errormsg.OPERATE_TOO_FAST,
                        'char_id': char_id,
                        'func_name': func_name,
                        'error_msg': 'Operate Too Fast, Return from cache',
                        'occurred_at': arrow.utcnow().to(TIME_ZONE).format('YYYY-MM-DD HH:mm:ss')
                    }

                    logger.info("Operate Guard. Char {0} operate {1} too fast. Return result from cache.".format(char_id, func_name),
                                extra=extra
                                )
                    return data

                data = func(request, *args, **kwargs)
                cache.set(redis_key, data, expire=interval)
                return data
            else:
                x = cache.get(redis_key)
                if x:
                    raise SanguoException(
                        errormsg.OPERATE_TOO_FAST,
                        char_id,
                        "Operate Guard",
                        "operate {0} too fast".format(func_name)
                    )

                cache.set(redis_key, 1, expire=interval)
                return func(request, *args, **kwargs)

        return wrap
    return deco


def function_check(func_id, mute=False):
    def deco(func):
        def wrap(request, *args, **kwargs):
            if not func_opened(request._char_id, func_id):
                if mute:
                    return None
                raise SanguoException(
                    errormsg.FUNC_FREEZE,
                    request._char_id,
                    "Function Open Check",
                    "func {0} freeze".format(func_id)
                )
            return func(request, *args, **kwargs)
        return wrap
    return deco


def passport(callable_checker, error_code, func_name, char_id_attr_name='char_id'):
    def deco(func):
        def wrap(obj, *args, **kwargs):
            char_id = getattr(obj, char_id_attr_name)
            if not callable_checker(char_id):
                raise SanguoException(
                    error_code,
                    char_id,
                    func_name,
                    "passport not ok"
                )

            return func(obj, *args, **kwargs)
        return wrap
    return deco
