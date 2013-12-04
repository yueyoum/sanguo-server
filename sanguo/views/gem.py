from django.http import HttpResponse

from core.gem import merge_gem
from core.exception import SanguoViewException

from core.mongoscheme import MongoChar

from protomsg import (
    MergeGemResponse,
)


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
    
    
#def sell(request):
#    req = request._proto
#    print req
#    
#    _, _, char_id = request._decrypted_session.split(':')
#    char_id = int(char_id)
#    
#    mongo_char = MongoChar.objects.only('gems').get(id=char_id)
#    