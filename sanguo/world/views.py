# -*- coding: utf-8 -*-
from django.http import HttpResponse

from models import Server

from msg.account_pb2 import (
        GetServerListResponse,
        )
from msg.world_pb2 import Server as ServerMsg

from utils import pack_msg


def get_server_list(request):
    req = request._proto
    print req

    servers = Server.objects.all()
    response = GetServerListResponse()
    top = servers[0]

    response.ret = 0
    response.top.id, response.top.name, response.top.status, response.top.have_char =\
            top.id, top.name, ServerMsg.GOOD, False

    for server in servers:
        s = response.servers.add()
        s.id, s.name, s.status, s.have_char = \
                server.id, server.name, ServerMsg.GOOD, False

    data = pack_msg(response)

    return HttpResponse(data, content_type='text/plain')

