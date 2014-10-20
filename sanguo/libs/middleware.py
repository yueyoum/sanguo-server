# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/10/14'

from django.http import HttpResponse
from django.conf import settings

from libs import (
    NUM_FIELD,
    METHOD_POST,
    MSG_TYPE_EMPTY_SESSION,
    pack_msg,
    unpack_msg,
    crypto,
    MAX_NUM_FIELD_AMOUNT,
)
from libs.session import session_loads, EmptyGameSession
from libs.exception import VersionCheckFailure

import protomsg
from protomsg import COMMAND_REQUEST, COMMAND_TYPE

class RequestFilter(object):
    def process_request(self, request):
        path = request.path

        if path.startswith('/api/') or path.startswith('/system/') or path.startswith('/callback/'):
            return None

        if request.method != METHOD_POST:
            return HttpResponse(status=403)

        data = request.body

        num_of_msgs = NUM_FIELD.unpack(data[:4])[0]
        if num_of_msgs > MAX_NUM_FIELD_AMOUNT:
            print "NUM_OF_MSGS TOO BIG! {0} > {1}".format(num_of_msgs, MAX_NUM_FIELD_AMOUNT)
            return HttpResponse(status=403)

        data = data[4:]

        for i in xrange(num_of_msgs):
            msg_id, msg, data = unpack_msg(data)
            if msg_id == 51:
                proto = protomsg.VersionCheckRequest()
                try:
                    proto.ParseFromString(msg)
                except:
                    print "PARSE VERSION_CHECK_REQUEST ERROR"
                    return HttpResponse(status=403)

                if proto.version != settings.SERVER_VERSION:
                    print "==== VERSION CHECK FAILURE ===="
                    print "==== client: {0} ====".format(proto.version)
                    print "==== server: {0} ====".format(settings.SERVER_VERSION)

                    raise VersionCheckFailure()

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
                request._char_id = request._game_session.char_id

                print "CHAR ID =", request._char_id
