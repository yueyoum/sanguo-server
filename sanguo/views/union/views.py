# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-1'

from utils.decorate import message_response

from core.union import UnionManager

@message_response("UnionCreateResponse")
def create(request):
    req = request._proto
    char_id = request._char_id

    m = UnionManager(char_id)
    m.create(req.name)
    return None


@message_response("UnionModifyResponse")
def modify(request):
    req = request._proto
    char_id = request._char_id

    m = UnionManager(char_id)
    m.modify(req.id, req.bulletin)
    return None


@message_response("UnionApplyResponse")
def apply_join(request):
    req = request._proto
    char_id = request._char_id

    m = UnionManager(char_id)
    m.apply_join(req.id)
    return None


@message_response("UnionAgreeResponse")
def agree_join(request):
    req = request._proto
    char_id = request._char_id

    m = UnionManager(char_id)
    m.agree_join(req.char_id)
    return None

@message_response("UnionRefuseResponse")
def refuse_join(request):
    req = request._proto
    char_id = request._char_id

    m = UnionManager(char_id)
    m.refuse_join(req.char_id)
    return None


@message_response("UnionListResponse")
def get_list(request):
    char_id = request._char_id

    m = UnionManager(char_id)
    m.send_list_notify()
    return None
