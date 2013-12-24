from django.http import HttpResponse

from core.exception import SanguoViewException
from core.gem import merge_gem
from core.mongoscheme import MongoChar
from protomsg import MergeGemResponse
from utils import pack_msg


def merge(request):
    req = request._proto
    char_id = request._char_id
    
    merge_gem(
        req.id,
        req.amount,
        req.using_sycee,
        char_id
    )
    
    response = MergeGemResponse()
    response.ret = 0
    data = pack_msg(response)
    return HttpResponse(data, content_type='text/plain')
