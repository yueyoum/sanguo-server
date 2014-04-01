# -*- coding: utf-8 -*-
from protomsg import Server as ServerMsg
from apps.character.models import Character as ModelCharacter

from preset.data import SERVERS

def server_list(user=None):
    user_servers = []
    if user:
        user_servers = ModelCharacter.objects.only('server_id').filter(
            account_id=user.id).values_list('server_id', flat=True)

    top = None
    all_servers = []
    for sid, s in SERVERS.items():
        _s = ServerMsg()
        _s.id = sid
        _s.name = s.name
        # FIXME status
        _s.status = ServerMsg.GOOD
        _s.have_char = sid in user_servers

        # FIXME
        _s.url = 'http://work.mztimes.com'
        _s.port = 8004

        if user and user.last_server_id and user.last_server_id == sid:
            top = _s

        all_servers.append(_s)

    if top is None:
        top = all_servers[-1]

    return top, all_servers

