# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'


from utils.decorate import message_response, function_check
from core.hero import Hero, char_heros_dict, recruit_hero
from core.exception import SanguoException
from preset import errormsg
from utils import pack_msg
from protomsg import HeroStepUpResponse


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

    response = HeroStepUpResponse()
    response.ret = 0
    response.id = _id
    return pack_msg(response)

@message_response("HeroRecruitResponse")
def recruit(request):
    recruit_hero(request._char_id, request._proto.id)
    return None

