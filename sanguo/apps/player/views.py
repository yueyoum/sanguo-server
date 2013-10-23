# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.utils import timezone

from models import User
from apps.character.models import Character
from utils import crypto

from protomsg import (
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

    if User.objects.filter(email=req.email).exists():
        raise SanguoViewException(100, req.session, "RegisterResponse")

    try:
        user = User.objects.get(device_token=req.device_token)
        if user.email:
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
    
    need_create_char = None
    if req.anonymous.device_token:
        try:
            user = User.objects.get(device_token=req.anonymous.device_token)
        except User.DoesNotExist:
            user = create_new_user(device_token=req.anonymous.device_token)
            need_create_char = True
    else:
        if not req.regular.email or not req.regular.password:
            return HttpResponse(status=403)
        try:
            user = User.objects.get(email = req.regular.email)
            if user.passwd != req.regular.password:
                raise SanguoViewException(150, req.session, "StartGameResponse")
        except User.DoesNotExist:
            raise SanguoViewException(151, req.session, "StartGameResponse")

    user.last_login = timezone.now()
    user.save()

    if need_create_char is None:
        _exists = Character.objects.filter(
                account_id=user.id,
                server_id = req.server_id
                ).exists()
        need_create_char = not _exists

    if not need_create_char:
        # TODO send notify
        pass

    session = crypto.encrypt("%d:%d" % (user.id, req.server_id))

    response = StartGameResponse()
    response.ret = 0
    response.need_create_new_char = need_create_char

    data = pack_msg(response, session)
    return HttpResponse(data, content_type='text/plain')


