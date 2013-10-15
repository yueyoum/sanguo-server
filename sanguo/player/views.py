import struct

from django.http import HttpResponse
from django.utils import timezone

from models import User

from msg.account_pb2 import (
        StartGameRequest,
        StartGameResponse,
        )


NUM_FIELD = struct.Struct('>i')

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

    data = response.SerializeToString()
    num_of_msgs = NUM_FIELD.pack(1)
    id_of_msg = NUM_FIELD.pack(1001)
    len_of_msg = NUM_FIELD.pack(len(data))

    data = '%s%s%s%s' % (num_of_msgs, id_of_msg, len_of_msg, data)
    
    return HttpResponse(
            data,
            content_type='text/plain'
            )

