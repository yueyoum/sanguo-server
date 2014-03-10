import logging

from django.http import HttpResponse

from core.exception import SanguoException, InvalidOperate
from utils import cache
from utils import pack_msg
import protomsg


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
                return HttpResponse(res, content_type='text/plain')
            except SanguoException as e:
                m.ret = e.error_id
                return HttpResponse(pack_msg(m), content_type='text/plain')

        return wrap
    return deco


def operate_guard(func_name, interval, keep_result=False):
    def deco(func):
        def wrap(request, *args, **kwargs):
            char_id = getattr(request, 'char_id', None)
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
                    raise InvalidOperate("Operate Guard. Char {0} operate {1} too fast".format(char_id, func_name))

                cache.set(redis_key, 1, expire=interval)
                return func(request, *args, **kwargs)

        return wrap
    return deco


