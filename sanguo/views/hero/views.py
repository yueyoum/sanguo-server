# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '4/9/14'


from utils.decorate import message_response, function_check
from core.hero import Hero, char_heros_dict, recruit_hero, break_hero
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
    response.step = h.step
    response.max_socket_amount = h.max_socket_amount
    response.current_socket_amount = h.current_socket_amount
    return pack_msg(response)

@message_response("HeroRecruitResponse")
def recruit(request):
    recruit_hero(request._char_id, request._proto.id)
    return None


@message_response("HeroWuXingUpdateResponse")
def wuxing_update(request):
    req = request._proto

    hero_id = req.hero_id
    wuxing_id = req.wuxing_id
    souls = [(s.id, s.amount) for s in req.souls]

    h = Hero(hero_id)
    h.wuxing_update(wuxing_id, souls)
    return None

@message_response("HeroBreakResponse")
def hero_break(request):
    char_id = request._char_id
    hero_id = request._proto.hero_id

    break_hero(char_id, hero_id)
    return None

