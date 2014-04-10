from core.attachment import Attachment

from libs import pack_msg
from utils.decorate import message_response

from protomsg import PrizeResponse

@message_response("PrizeResponse")
def prize_get(request):
    req = request._proto
    char_id = request._char_id

    attachment = Attachment(char_id)
    att_msg = attachment.get_attachment(req.prize.id, req.prize.param)

    response = PrizeResponse()
    response.ret = 0
    response.prize.MergeFrom(req.prize)
    response.drop.MergeFrom(att_msg)
    return pack_msg(response)
