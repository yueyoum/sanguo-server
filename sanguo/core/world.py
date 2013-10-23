# -*- coding: utf-8 -*-
from apps.world.models import Server

from protomsg import Server as ServerMsg



def server_list(uid=None):
    servers = Server.objects.all()

    all_servers = []
    for s in servers:
        _s = ServerMsg()
        _s.id, _s.name, _s.status, _s.have_char = \
                s.id, s.name, ServerMsg.GOOD, False

        all_servers.append(_s)

    return all_servers[0], all_servers

