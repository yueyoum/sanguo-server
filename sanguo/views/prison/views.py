# -*- coding: utf-8 -*-

from utils.decorate import message_response
from utils import pack_msg

from core.prison import Prison

from protomsg import PrisonerGetResponse, PrisonerReleaseResponse, PrisonerKillResponse

@message_response("PrisonerGetResponse")
def prisoner_get(request):
    req = request._proto
    p = Prison(request._char_id)
    got = p.prisoner_get(req.id, [i for i in req.treasure_ids])

    msg = PrisonerGetResponse()
    msg.ret = 0
    msg.success = got
    return pack_msg(msg)


@message_response("PrisonerReleaseResponse")
def prisoner_release(request):
    req = request._proto

    p = Prison(request._char_id)
    gold, stuffs = p.release(req.id)

    response = PrisonerReleaseResponse()
    response.ret = 0
    response.reward.gold = gold
    for _id, amount in stuffs:
        s = response.reward.stuffs.add()
        s.id = _id
        s.amount = amount

    return pack_msg(response)


@message_response("PrisonerKillResponse")
def prisoner_kill(request):
    req = request._proto

    p = Prison(request._char_id)
    stuffs = p.kill(req.id)

    response = PrisonerKillResponse()
    response.ret = 0
    for _id, amount in stuffs:
        s = response.reward.stuffs.add()
        s.id = _id
        s.amount = amount

    return pack_msg(response)





