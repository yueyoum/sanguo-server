# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.utils import timezone

from models import User

from msg.account_pb2 import (
        StartGameResponse,
        RegisterResponse,
        )

from core.world import server_list
from utils import pack_msg

def register(request):
    req = request._proto
    print req

    ret = 0
    try:
        user = User.objects.get(device_token=req.device_token)
        if user.email:
            print "Already Bind email"
            ret = 2
        else:
            print "Bind"
            user.email = req.email
            user.passwd = req.password
            user.save()
    except User.DoesNotExist:
        print "New User"
        if User.objects.filter(email=req.email).exists():
            ret = 1
        else:
            user = User.objects.create(
                    email = req.email,
                    passwd = req.password,
                    device_token = req.device_token,
                    last_login = timezone.now(),
                    game_session = ""
                    )

    response = RegisterResponse()
    response.ret = ret
    if ret == 0:
        response.email = req.email
        response.password = req.password
        
        top, all_servers = server_list()
        response.top.MergeFrom(top)
        for server in all_servers:
            s = response.servers.add()
            s.MergeFrom(server)


    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')




def login(request):
    req = request._proto
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


