# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.utils import timezone

from models import User

from msg.account_pb2 import (
        StartGameResponse,
        RegisterResponse,
        )

from core.world import server_list
from core.exception import SanguoViewException
from utils import pack_msg

def create_new_user(**kwargs):
    email = kwargs.get('email', '')
    passwd = kwargs.get('password', '')
    device_token = kwargs.get('device_token', '')

    if not email and not passwd and not device_token:
        raise ValueError("Can not create user with Empty values")

    user = User.objects.create(
            email = email,
            passwd = passwd,
            device_token = device_token
            )
    return user



def register(request):
    req = request._proto
    print req

    if not req.email or not req.password or not req.device_token:
        return HttpResponse(status=403)

    try:
        user = User.objects.get(device_token=req.device_token)
        if user.email:
            if user.email == req.email:
                print "Error: Already bind"
                raise SanguoViewException("RegisterResponse", 100)
            else:
                print "Already Bind email, Create New User"
                user = create_new_user(
                        email = req.email,
                        password = req.password,
                        device_token = req.device_token
                        )
        else:
            print "Bind"
            user.email = req.email
            user.passwd = req.password
            user.save()
    except User.DoesNotExist:
        print "New User"
        if User.objects.filter(email=req.email).exists():
            raise SanguoViewException("RegisterResponse", 101)
        else:
            user = create_new_user(
                    email = req.email,
                    password = req.password,
                    device_token = req.device_token
                    )

    response = RegisterResponse()
    response.ret = 0
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
            user = create_new_user(device_token=req.anonymous.device_token)
    else:
        if not req.regular.email or not req.regular.password:
            return HttpResponse(status=403)
        try:
            user = User.objects.get(email = req.regular.email)
            if user.passwd != req.regular.password:
                raise SanguoViewException("StartGameResponse", 102)
        except User.DoesNotExist:
            raise SanguoViewException("StartGameResponse", 103)

    user.last_login = timezone.now()
    user.save()

    response = StartGameResponse()
    response.ret = 0
    response.session = "test!"

    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')


