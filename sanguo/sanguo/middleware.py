
from django.http import HttpResponse

import protomsg

from core.server import server
from core.version import version
from core.msgpipe import message_get
from core.activeplayers import ActivePlayers, Player
from preset import errormsg
from utils import pack_msg
from protomsg import ReLoginResponse, VersionCheckResponse

### FOR DEBUG
from utils import app_test_helper

RESPONSE_NOTIFY_TYPE_REV = {v: k for k, v in protomsg.RESPONSE_NOTIFY_TYPE.items()}


from libs.middleware import RequestFilter
from libs import NUM_FIELD
from libs.exception import VersionCheckFailure


class UnpackAndVerifyData(RequestFilter):
    def process_request(self, request):
        try:
            super(UnpackAndVerifyData, self).process_request(request)
        except VersionCheckFailure:
            version_msg = VersionCheckResponse()
            version_msg.ret = 0
            version_msg.version = version.version
            return HttpResponse(pack_msg(version_msg), content_type='text/plain')

        if request.path.startswith('/api/'):
            return

        if not server.active:
            return HttpResponse(status=502)

        char_id = getattr(request, '_char_id', None)
        if char_id:
            if request.path != '/resume/':
                p = Player(char_id)
                login_id = p.get_login_id()
                if not login_id:
                    msg = ReLoginResponse()
                    msg.ret = errormsg.SESSION_EXPIRE
                    data = pack_msg(msg)
                    return HttpResponse(data, content_type='text/plain')

                if login_id != request._game_session.login_id:
                    # NEED RE LOGIN
                    msg = ReLoginResponse()
                    msg.ret = errormsg.LOGIN_RE
                    data = pack_msg(msg)
                    return HttpResponse(data, content_type='text/plain')

                p.refresh()

            ap = ActivePlayers()
            ap.set(request._char_id)


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
