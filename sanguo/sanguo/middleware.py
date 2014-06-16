
from django.http import HttpResponse

import protomsg

from core.msgpipe import message_get, message_clean
from core.activeplayers import ActivePlayers

### FOR DEBUG
from utils import app_test_helper

RESPONSE_NOTIFY_TYPE_REV = {v: k for k, v in protomsg.RESPONSE_NOTIFY_TYPE.items()}


from libs.middleware import RequestFilter
from libs import NUM_FIELD


class UnpackAndVerifyData(RequestFilter):
    def process_request(self, request):
        super(UnpackAndVerifyData, self).process_request(request)

        if request.path.startswith('/api/'):
            return

        server_id = getattr(request, '_server_id', None)
        char_id = getattr(request, 'char_id', None)
        if server_id and char_id:
            ap = ActivePlayers(request._server_id)
            ap.set(request._char_id)

        if char_id and request.path == '/player/login/':
            message_clean(char_id)


class PackMessageData(object):
    def process_response(self, request, response):
        if response.status_code != 200:
            return response

        if request.path.startswith('/api/'):
            return response

        char_id = getattr(request, '_char_id', None)
        if char_id:
            other_msgs = message_get(char_id)
        else:
            other_msgs = []

        if not response.content:
            num_of_msgs = len(other_msgs)
            data = '%s%s' % (
                NUM_FIELD.pack(num_of_msgs),
                ''.join(other_msgs)
            )
        else:
            ret_msg_amount = getattr(response, '_msg_amount', 1)
            num_of_msgs = len(other_msgs) + ret_msg_amount
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
        # DEBUG END
        return HttpResponse(data, content_type='text/plain')
