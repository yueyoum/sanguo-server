# -*- coding: utf-8 -*-

from utils.decorate import message_response
from utils import pack_msg

from core.prison import Prison

from protomsg import PrisonerGetResponse

@message_response("PrisonIncrAmountResponse")
def incr_prisoners_amount(request):
    p = Prison(request._char_id)
    p.incr_amount()
    return None


@message_response("PrisonerAddProbResponse")
def prisoner_add_prob(request):
    req = request._proto
    p = Prison(request)
    p.prisoner_incr_prob(req.id)
    return None

@message_response("PrisonerGetResponse")
def prisoner_get(request):
    req = request._proto
    p = Prison(request._char_id)
    got = p.prisoner_get(req.id)

    msg = PrisonerGetResponse()
    msg.success = got
    return pack_msg(msg)
