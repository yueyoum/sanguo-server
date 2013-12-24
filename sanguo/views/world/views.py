from django.http import HttpResponse

from apps.player.models import User
from protomsg import GetServerListResponse
from core.world import server_list
from core.exception import BadMessage
from utils import pack_msg

def get_server_list(request):
    req = request._proto
    
    if req.anonymous.device_token:
        try:
            user = User.objects.get(device_token=req.anonymous.device_token)
        except User.DoesNotExist:
            user = None
    else:
        if not req.regular.email or not req.regular.password:
            raise BadMessage("GetServerListResponse")
        try:
            user = User.objects.get(email=req.regular.email)
            if user.passwd != req.regular.password:
                user = None
        except User.DoesNotExist:
            user = None
    
    top, all_servers = server_list(user)
    
    res = GetServerListResponse()
    res.ret = 0
    
    res.top.id, res.top.name, res.top.status, res.top.have_char =\
            top.id, top.name, top.status, top.have_char
    
    for server in all_servers:
        s = res.servers.add()
        s.id, s.name, s.status, s.have_char = \
            server.id, server.name, server.status, server.have_char
    
    data = pack_msg(res)
    return HttpResponse(data, content_type='text/plain')
    
