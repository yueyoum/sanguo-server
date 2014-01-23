# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/23/14'

from utils.decorate import message_response

from core.heropanel import HeroPanel

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
    p.open(req.id)
    return None