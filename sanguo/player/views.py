# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.utils import timezone

from models import User

from msg.account_pb2 import (
        StartGameResponse,
        )

from utils import pack_msg


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


