# -*- coding: utf-8 -*-
from apps.world.models import Server

from msg.world_pb2 import Server as ServerMsg



def server_list(uid=None):
    servers = Server.objects.all()
    top = servers[0]

    top = ServerMsg()
    top.id, top.name, top.status, top.have_char = \
            servers[0].id, servers[0].name, ServerMsg.GOOD, False

    all_servers = []
    for s in servers:
        _s = ServerMsg()
        _s.id, _s.name, _s.status, _s.have_char = \
                s.id, s.name, ServerMsg.GOOD, False

        all_servers.append(_s)

    return top, all_servers
