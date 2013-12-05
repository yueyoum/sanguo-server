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
from core.signals import login_signal
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

    if not req.email or not req.password or not req.device_token:
        return HttpResponse(status=403)

    if User.objects.filter(email=req.email).exists():
        raise SanguoViewException(100, "RegisterResponse")

    users = User.objects.filter(device_token=req.device_token)
    users_count = users.count()

    if users_count == 0:
        print "New User"
        user = create_new_user(
                email = req.email,
                password = req.password,
                device_token = req.device_token
                )
    elif users_count == 1:
        user  = users[0]
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
    else:
        print "Registed multi times, create new user"
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
    
    need_create_new_char = None
    if req.anonymous.device_token:
        users = User.objects.filter(device_token=req.anonymous.device_token)
        users_count = users.count()

        if users_count == 0:
            user = create_new_user(device_token=req.anonymous.device_token)
            need_create_new_char = True
        elif users_count == 1:
            user = users[0]
            if user.email:
                user = create_new_user(device_token=req.anonymous.device_token)
                need_create_new_char = True
        else:
            user = create_new_user(device_token=req.anonymous.device_token)
            need_create_new_char = True
    else:
        if not req.regular.email or not req.regular.password:
            return HttpResponse(status=403)
        try:
            user = User.objects.get(email = req.regular.email)
            if user.passwd != req.regular.password:
                raise SanguoViewException(150, "StartGameResponse")
        except User.DoesNotExist:
            raise SanguoViewException(151, "StartGameResponse")

    user.last_login = timezone.now()
    user.save()
    
    request._account_id = user.id
    request._server_id = req.server_id

    if need_create_new_char is None:
        try:
            char = Character.objects.get(
                    account_id = user.id,
                    server_id = req.server_id
                    )
            need_create_new_char = False
        except Character.DoesNotExist:
            need_create_new_char = True


    if need_create_new_char:
        char_id = None
    else:
        char_id = char.id
        
    request._char_id = char_id

    login_signal.send(
        sender = None,
        account_id = request._account_id,
        server_id = request._server_id,
        char_obj = char if char_id else None
    )
    
    if char_id:
        session_str = '{0}:{1}'.format(request._account_id, request._server_id)
    else:
        session_str = '{0}:{1}:{2}'.format(
            request._account_id,
            request._server_id,
            request._char_id
        )

    session = crypto.encrypt(session_str)
    #if not need_create_new_char:
    #    login_notify(key, char)

    response = StartGameResponse()
    response.ret = 0
    if req.anonymous.device_token:
        response.anonymous.MergeFrom(req.anonymous)
    else:
        response.regular.MergeFrom(req.regular)
    response.need_create_new_char = need_create_new_char 

    data = pack_msg(response, session)
    return HttpResponse(data, content_type='text/plain')


