# -*- coding: utf-8 -*-
from django.http import HttpResponse

# from models import Server

from protomsg import (
        GetServerListResponse,
        )

from core.world import server_list
from utils import pack_msg


def get_server_list(request):
    req = request._proto
    print req

    top, all_servers = server_list()

    response = GetServerListResponse()

    response.ret = 0
    response.top.id, response.top.name, response.top.status, response.top.have_char =\
            top.id, top.name, top.status, top.have_char

    for server in all_servers:
        s = response.servers.add()
        s.id, s.name, s.status, s.have_char = \
                server.id, server.name, server.status, server.have_char

    data = pack_msg(response)

    return HttpResponse(data, content_type='text/plain')

