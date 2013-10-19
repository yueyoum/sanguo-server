import struct

from django.http import HttpResponse

import msg
from msg import REQUEST_TYPE

from core.exception import SanguoViewException
from utils import pack_msg

NUM_FIELD = struct.Struct('>i')


class UnpackAndVerifyData(object):
    def process_request(self, request):
        if request.path.startswith('/admin/'):
            return None

        data = request.body
        msg_id = NUM_FIELD.unpack(data[:4])
        msg_id = msg_id[0]

        msg_name, allowd_method = REQUEST_TYPE[msg_id]
        if request.method != allowd_method:
            return HttpResponse(status=403)

        proto = getattr(msg, msg_name)
        p = proto()
        p.ParseFromString(data[4:])
        
        game_session = getattr(p, 'session', None)
        if game_session:
            # TODO
            pass

        request._proto = p



class PackMessageData(object):
    def process_response(self, request, response):
        if request.path.startswith('/admin/'):
            return response

        if response.status_code != 200:
            return response

        # TODO get other messages
        other_msgs = []
        num_of_msgs = len(other_msgs) + 1

        data = '%s%s%s' % (
                NUM_FIELD.pack(num_of_msgs),
                response.content,
                ''.join(other_msgs)
                )

        return HttpResponse(data, content_type='text/plain')


class ViewExceptionHandler(object):
    def process_exception(self, request, exception):
        if isinstance(exception, SanguoViewException):
            Msg = getattr(msg, exception.response_msg_name)
            m = Msg()
            m.ret = exception.error_id

            data = pack_msg(m)
            return HttpResponse(data, content_type='text/plain')
        
        raise exception


