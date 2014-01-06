from django.http import HttpResponse

from core.exception import SanguoException
from utils import pack_msg
import protomsg



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