# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-1'

from utils.decorate import message_response
from utils import pack_msg

from core.union import UnionManager, UnionStore, UnionMember, UnionBattle, UnionBoss

from protomsg import UnionBattleStartResponse, UnionBattleRecordGetResponse, UnionBossBattleResponse


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

@message_response("UnionQuitResponse")
def quit(request):
    char_id = request._char_id

    m = UnionManager(char_id)
    m.quit()
    return None

@message_response("UnionMemberManageResponse")
def manage(request):
    req = request._proto
    char_id = request._char_id

    m = UnionManager(char_id)
    if req.action == 1:
        m.kickout(req.member_id)
    else:
        m.transfer(req.member_id)

    return None

@message_response("UnionStoreBuyResponse")
def store_buy(request):
    req = request._proto
    char_id = request._char_id

    s = UnionStore(char_id)
    s.buy(req.id, 1)
    return None

@message_response("UnionCheckinResponse")
def checkin(request):
    char_id = request._char_id
    m = UnionMember(char_id)
    m.checkin()
    return None


@message_response("UnionBattleBoardResponse")
def get_battle_board(request):
    char_id = request._char_id
    b = UnionBattle(char_id)
    return pack_msg(b.make_board_msg())


@message_response("UnionBattleStartResponse")
def battle_start(request):
    char_id = request._char_id
    b = UnionBattle(char_id)

    response = UnionBattleStartResponse()
    response.ret = 0
    response.record.MergeFrom(b.start_battle())
    return pack_msg(response)

@message_response("UnionBattleRecordGetResponse")
def get_records(request):
    char_id = request._char_id
    b = UnionBattle(char_id)

    response = UnionBattleRecordGetResponse()
    response.ret = 0
    records = b.get_records()
    for r in records:
        msg_r = response.records.add()
        msg_r.MergeFromString(r)

    return pack_msg(response)


@message_response("UnionBossResponse")
def get_union_boss(request):
    char_id = request._char_id

    b = UnionBoss(char_id)
    msg = b.make_boss_response()
    return pack_msg(msg)

@message_response("UnionBossGetLogResponse")
def get_union_boss_log(request):
    req = request._proto
    char_id = request._char_id

    b = UnionBoss(char_id)
    msg = b.make_log_message(req.boss_id)
    return pack_msg(msg)


@message_response("UnionBossStartResponse")
def union_boss_start(request):
    req = request._proto
    char_id = request._char_id
    b = UnionBoss(char_id)
    b.start(req.boss_id)
    return None

@message_response("UnionBossBattleResponse")
def union_boss_battle(request):
    req = request._proto
    char_id = request._char_id

    b = UnionBoss(char_id)
    msg = b.battle(req.boss_id)

    response = UnionBossBattleResponse()
    response.ret = 0
    response.battle.MergeFrom(msg)
    return pack_msg(response)


