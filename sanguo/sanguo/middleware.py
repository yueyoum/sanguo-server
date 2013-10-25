import struct
import traceback

from django.http import HttpResponse

import protomsg
from protomsg import REQUEST_TYPE

from core.exception import SanguoViewException
from core.drives import redis_client
from utils import crypto
from utils import pack_msg

NUM_FIELD = struct.Struct('>i')
EMPTY_SESSION_MSG_TYPE = set([100, 102, 105])


### FOR DEBUG
from utils import app_test_helper
RESPONSE_NOTIFY_TYPE_REV = {v: k for k, v in protomsg.RESPONSE_NOTIFY_TYPE.items()}


class UnpackAndVerifyData(object):
    def process_request(self, request):
        if request.path.startswith('/admin/'):
            return None

        if request.method != "POST":
            return HttpResponse(status=403)

        data = request.body
        msg_id = NUM_FIELD.unpack(data[:4])
        msg_id = msg_id[0]

        msg_name = REQUEST_TYPE[msg_id]

        proto = getattr(protomsg, msg_name)
        p = proto()
        p.ParseFromString(data[4:])
        
        game_session = p.session
        decrypted_session = ""
        if msg_id not in EMPTY_SESSION_MSG_TYPE:
            if not game_session:
                print "NO SESSION"
                return HttpResponse(status=403)
            try:
                decrypted_session = crypto.decrypt(game_session)
            except crypto.BadEncryptedText:
                print "BAD SESSION"
                return HttpResponse(status=403)

        request._proto = p
        request._decrypted_session = decrypted_session



class PackMessageData(object):
    def process_response(self, request, response):
        if response.status_code != 200:
            return response

        if request.path.startswith('/admin/'):
            return response

        key = getattr(request, '_decrypted_session', None) or getattr(
                response, '_redis_key', None
                )
        if key:
            pipeline = redis_client.pipeline()
            pipeline.lrange(key, 0, -1)
            pipeline.delete(key)
            other_msgs, _ = pipeline.execute()
        else:
            other_msgs = []

        if not response.content:
            num_of_msgs = len(other_msgs)
            data = '%s%s' % (
                    NUM_FIELD.pack(num_of_msgs),
                    ''.join(other_msgs)
                    )
        else:
            num_of_msgs = len(other_msgs) + 1
            data = '%s%s%s' % (
                    NUM_FIELD.pack(num_of_msgs),
                    response.content,
                    ''.join(other_msgs)
                    )

        # FOR DEBUG
        # print repr(data)
        _unpakced_data = app_test_helper.unpack_data(data)
        _msg_type = [RESPONSE_NOTIFY_TYPE_REV[a] for a, b, c in _unpakced_data]
        print _msg_type
        return HttpResponse(data, content_type='text/plain')


class ViewExceptionHandler(object):
    def process_exception(self, request, exception):
        if isinstance(exception, SanguoViewException):
            proto = getattr(protomsg, exception.response_msg_name)
            m = proto()
            m.ret = exception.error_id

            data = pack_msg(m, exception.session)
            return HttpResponse(data, content_type='text/plain')
        
        traceback.print_exc()
        raise exception


