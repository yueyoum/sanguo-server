# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.utils import timezone

from models import User

from msg.account_pb2 import (
        StartGameRequest,
        StartGameResponse,
        Server,
        GetServerListRequest,
        GetServerListResponse,
        )

from utils import pack_msg


def login(request):
    if request.method != 'POST':
        return HttpResponse(status=403)

    data = request.body

    req = StartGameRequest()
    req.ParseFromString(data)

    print req
    
    if req.anonymous.device_token:
        try:
            user = User.objects.get(device_token=req.anonymous.device_token)
        except User.DoesNotExist:
            user = User.objects.create(
                    device_token = req.anonymous.device_token,
                    last_login = timezone.now(),
                    game_session = ""
                    )

    else:
        try:
            user = User.objects.get(
                    email = req.regular.email,
                    passwd = req.regular.password
                    )
        except User.DoesNotExist:
            user = User.objects.create(
                    email = req.regular.email,
                    passwd = req.regular.password,
                    last_login = timezone.now(),
                    game_session = ""
                    )

    user.last_login = timezone.now()
    user.save()


    response = StartGameResponse()
    response.ret = 0
    response.session = "test!"

    data = pack_msg(response)

    return HttpResponse(data, content_type='text/plain')


def get_server_list(request):
    servers = [
            (1, "第一服务器", Server.GOOD, False),
            (1, "第二服务器", Server.GOOD, False),
            (1, "第三服务器", Server.BUSY, False),
            (1, "第四服务器", Server.MAINTAIN, False),
            (1, "第五服务器", Server.GOOD, False),
            ]

    response = GetServerListResponse()
    top = servers[0]

    response.ret = 0
    response.top.id, response.top.name, response.top.status, response.top.have_char =\
            top

    for server in servers:
        s = response.servers.add()
        s.id, s.name, s.status, s.have_char = server

    return HttpResponse(
            response.SerializeToString(),
            content_type='text/plain'
            )


