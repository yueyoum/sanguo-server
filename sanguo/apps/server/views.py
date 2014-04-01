from apps.account.models import Account
from core.world import server_list
from core.exception import BadMessage
from utils import pack_msg
from utils.decorate import message_response

from protomsg import GetServerListResponse

@message_response("GetServerListResponse")
def get_server_list(request):
    req = request._proto

    if req.anonymous.device_token:
        try:
            user = Account.objects.get(device_token=req.anonymous.device_token)
        except Account.DoesNotExist:
            user = None
    else:
        if not req.regular.email or not req.regular.password:
            raise BadMessage()
        try:
            user = Account.objects.get(email=req.regular.email)
            if user.passwd != req.regular.password:
                user = None
        except Account.DoesNotExist:
            user = None

    top, all_servers = server_list(user)

    res = GetServerListResponse()
    res.ret = 0

    res.top.MergeFrom(top)
    for server in all_servers:
        s = res.servers.add()
        s.MergeFrom(server)

    return pack_msg(res)

