# -*- coding: utf-8 -*-
import requests

from protomsg import Server as ServerMsg

# from preset.data import SERVERS
#
# from django.conf import settings
#
# def server_list(user=None):
#
#     if user:
#         params = {'account_id': user.id}
#     else:
#         params = {}
#
#     x = requests.get(settings.GATE_URL + '/api/server-list/', params=params)
#     servers = x.json()
#
#     top = None
#     all_servers = []
#     for s in servers['data']:
#         _s = ServerMsg()
#         _s.id = s['id']
#         _s.name = s['name']
#         _s.status = s['status']
#         _s.have_char = s['have_char']
#         _s.url = s['url']
#         _s.port = s['port']
#
#         all_servers.append(_s)
#
#         if user and user.last_server_id == s['id']:
#             top = _s
#
#     if top is None:
#         top = all_servers[-1]
#
#     return top, all_servers
#
