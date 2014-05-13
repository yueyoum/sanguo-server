# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'


from utils.decorate import message_response, function_check
from core.hero import Hero, char_heros_dict
from core.exception import SanguoException
from preset import errormsg


@message_response("HeroStepUpResponse")
@function_check(3)
def step_up(request):
    char_id = request._char_id
    heros_dict = char_heros_dict(char_id)

    req = request._proto
    _id = req.id

    if _id not in heros_dict:
        raise SanguoException(
            errormsg.HERO_NOT_EXSIT,
            char_id,
            "Hero Step Up",
            "hero {0} not belong to char {1}".format(_id, char_id)
        )

    h = Hero(_id)
    h.step_up()
    return None
