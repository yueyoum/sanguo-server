# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'


from utils.decorate import message_response
from core.character import Char
from core.hero import Hero
from core.exception import InvalidOperate


@message_response("HeroStepUpResponse")
def step_up(request):
    char_id = request._char_id
    char = Char(char_id)
    heros_dict = char.heros_dict

    _id = request._proto.id

    if _id not in heros_dict:
        raise InvalidOperate("Hero Step Up: Char {0} Try to up a NONE exist hero: {1}".format(
            char_id, _id
        ))

    h = Hero(_id)
    h.step_up()
    return None
