# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/10/14'

from django.http import HttpResponse

from libs import (
    NUM_FIELD,
    METHOD_POST,
    MSG_TYPE_EMPTY_SESSION,
    unpack_msg,
    crypto,
)
from libs.session import session_loads, EmptyGameSession

import protomsg
from protomsg import COMMAND_REQUEST, COMMAND_TYPE

class RequestFilter(object):
    def process_request(self, request):
        if request.method != METHOD_POST:
            return HttpResponse(status=403)

        path = request.path

        if path.startswith('/api/'):
            return None

        data = request.body

        num_of_msgs = NUM_FIELD.unpack(data[:4])[0]
        data = data[4:]

        for i in range(num_of_msgs):
            msg_id, msg, data = unpack_msg(data)
            if msg_id == 51:
                # TODO Check Version
                pass
            else:
                if getattr(request, '_proto', None) is not None:
                    continue

                if COMMAND_TYPE[path] != msg_id:
                    print "COMMAND TYPE NOT MATCH", path, msg_id
                    return HttpResponse(status=403)

                msg_name = COMMAND_REQUEST[path]
                proto = getattr(protomsg, msg_name)
                p = proto()
                try:
                    p.ParseFromString(msg)
                except:
                    print "PARSE PROTO ERROR"
                    return HttpResponse(status=403)

                print p

                game_session = p.session

                if msg_id in MSG_TYPE_EMPTY_SESSION:
                    decrypted_session = EmptyGameSession
                else:
                    try:
                        decrypted_session = crypto.decrypt(game_session)
                    except crypto.BadEncryptedText:
                        print "BAD SESSION"
                        return HttpResponse(status=403)
                    decrypted_session = session_loads(decrypted_session)

                request._proto = p
                request._game_session = decrypted_session

                request._account_id = request._game_session.account_id
                request._server_id = request._game_session.server_id
                request._char_id = request._game_session._char_id

                print "CHAR ID =", request._char_id

                # len_of_splited_session = len(splited_session)
                # if len_of_splited_session == 1:
                #     request._account_id = None
                #     request._server_id = None
                #     request._char_id = None
                # elif len_of_splited_session == 2:
                #     request._account_id = int(splited_session[0])
                #     request._server_id = int(splited_session[1])
                #     request._char_id = None
                # else:
                #     request._account_id = int(splited_session[0])
                #     request._server_id = int(splited_session[1])
                #     request._char_id = int(splited_session[2])
                #     print "CHAR ID =", request._char_id
