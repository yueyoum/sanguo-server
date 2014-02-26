import struct

from django.http import HttpResponse

import protomsg
from protomsg import REQUEST_TYPE

#from core.rabbit import rabbit
from utils import crypto
from core.msgpipe import message_get
from core.timercheck import timercheck
from core.activeplayers import ActivePlayers

NUM_FIELD = struct.Struct('>i')
EMPTY_SESSION_MSG_TYPE = set([100, 102, 105])


### FOR DEBUG
from utils import app_test_helper

RESPONSE_NOTIFY_TYPE_REV = {v: k for k, v in protomsg.RESPONSE_NOTIFY_TYPE.items()}


def _unpack(res):
    msg_id = NUM_FIELD.unpack(res[:4])[0]
    res = res[4:]
    len_of_msg = NUM_FIELD.unpack(res[:4])[0]
    res = res[4:]
    return msg_id, res[:len_of_msg], res[len_of_msg:]


class UnpackAndVerifyData(object):
    def process_request(self, request):
        # if request.path.startswith('/admin/'):
        #     return None

        if request.method != "POST":
            return HttpResponse(status=403)

        data = request.body

        num_of_msgs = NUM_FIELD.unpack(data[:4])[0]
        data = data[4:]

        for i in range(num_of_msgs):
            msg_id, msg, data = _unpack(data)
            if msg_id == 51:
                # TODO Check Version
                pass
            else:
                if getattr(request, '_proto', None) is not None:
                    continue

                msg_name = REQUEST_TYPE[msg_id]
                proto = getattr(protomsg, msg_name)
                p = proto()
                p.ParseFromString(msg)

                print p

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
                request._session = decrypted_session

                splited_session = decrypted_session.split(':')
                len_of_splited_session = len(splited_session)
                if len_of_splited_session == 1:
                    request._account_id = None
                    request._server_id = None
                    request._char_id = None
                elif len_of_splited_session == 2:
                    request._account_id = int(splited_session[0])
                    request._server_id = int(splited_session[1])
                    request._char_id = None
                else:
                    request._account_id = int(splited_session[0])
                    request._server_id = int(splited_session[1])
                    request._char_id = int(splited_session[2])
                    print "CHAR ID =", request._char_id

        timercheck.check(request._char_id)
        ap = ActivePlayers(request._server_id)
        ap.set(request._char_id)


_BIND = set()


class PackMessageData(object):
    def process_response(self, request, response):
        if response.status_code != 200:
            return response

        # if request.path.startswith('/admin/'):
        #     return response

        char_id = getattr(request, '_char_id', None)
        if char_id:
            #if char_id not in _BIND:
            #    rabbit.bind(char_id, request._server_id)
            #    _BIND.add(char_id)

            #other_msgs = rabbit.message_get_all(char_id)
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
        # DEBUG END
        return HttpResponse(data, content_type='text/plain')

#
# class ViewExceptionHandler(object):
#     def process_exception(self, request, exception):
#         if isinstance(exception, SanguoException):
#             proto = getattr(protomsg, exception.response_msg_name)
#             m = proto()
#             m.ret = exception.error_id
#
#             data = pack_msg(m)
#             return HttpResponse(data, content_type='text/plain')
#
#         traceback.print_exc()
#         raise exception
#

