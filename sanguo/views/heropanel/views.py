# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/23/14'

from utils.decorate import message_response
from utils import pack_msg

from core.heropanel import HeroPanel

from protomsg import GetHeroResponse


@message_response("GetHeroStartResponse")
def start(request):
    p = HeroPanel(request._char_id)
    p.start()
    return None


@message_response("GetHeroRefreshResponse")
def refresh(request):
    p = HeroPanel(request._char_id)
    p.refresh()
    return None

@message_response("GetHeroResponse")
def open(request):
    req = request._proto
    p = HeroPanel(request._char_id)
    hero_oid = p.open(req.id)

    response = GetHeroResponse()
    response.ret = 0
    response.id = req.id
    response.hero_oid = hero_oid
    return pack_msg(response)
