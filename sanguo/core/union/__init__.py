# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-12-10'

def send_notify(char_id):
    from core.union.battle import UnionBattle
    from core.union.boss import UnionBoss
    from core.union.store import UnionStore
    from core.union.union import Union, UnionList, UnionOwner
    from core.union.member import Member

    # 工会列表
    UnionList.send_list_notify(char_id)
    # 个人信息
    Member(char_id).send_personal_notify()

    u = Union(char_id)
    # UnionNotify
    u.send_notify()
    if isinstance(u, UnionOwner):
        # 会长才能看见的申请者列表
        u.send_apply_list_notify()

    # 商店
    UnionStore(char_id).send_notify()
    # 工会战
    UnionBattle(char_id).send_notify()
