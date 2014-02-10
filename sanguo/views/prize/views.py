from core.exception import SanguoException
from core.stage import Hang

import protomsg

from utils import pack_msg
from utils.decorate import message_response

@message_response("PrizeResponse")
def prize_get(request):
    req = request._proto
    char_id = request._char_id

    prize_id = req.prize_id

    # XXX only support 1 now
    prize_id = 1

    hang = Hang(char_id)
    if not hang.hang:
        raise SanguoException(703)

    exp, gold, stuffs = hang.save_drop()
    hang.hang.delete()
    hang.send_notify()

    response = protomsg.PrizeResponse()
    response.ret = 0
    response.prize_id = 1
    response.drop.gold = gold
    response.drop.exp = exp
    for _id, amount in stuffs:
        s = response.drop.stuffs.add()
        s.id = _id
        s.amount = amount

    return pack_msg(response)
