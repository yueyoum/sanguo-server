import logging

from django.http import HttpResponse

from core.exception import SanguoException
from core.mongoscheme import MongoFunctionOpen
from utils import cache
from utils import pack_msg
import protomsg
from preset import errormsg

from libs.decorate import json_return

logger = logging.getLogger('sanguo')

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


def operate_guard(func_name, interval, keep_result=False):
    def deco(func):
        def wrap(request, *args, **kwargs):
            char_id = getattr(request, '_char_id', None)
            if not char_id:
                return func(request, *args, **kwargs)

            redis_key = 'opt:{0}:{1}'.format(func_name, char_id)
            if keep_result:
                data = cache.get(redis_key)
                if data:
                    logger.info("Operate Guard. Char {0} operate {1} too fast. Return result from cache.".format(char_id, func_name))
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


def function_check(func_id):
    def deco(func):
        def wrap(request, *args, **kwargs):
            fo = MongoFunctionOpen.objects.get(id=request._char_id)
            if func_id in fo.freeze:
                # FIXME error code
                raise SanguoException(
                    errormsg.FUNC_FREEZE,
                    request._char_id,
                    "Function Open Check",
                    "func {0} freeze".format(func_id)
                )
            return func(request, *args, **kwargs)
        return wrap
    return deco

