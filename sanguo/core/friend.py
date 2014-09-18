# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '12/31/13'

from mongoengine import DoesNotExist

from core.mongoscheme import MongoFriend, MongoCharacter
from core.character import Char, get_char_ids_by_level_range
from core.hero import Hero
from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.formation import Formation
from core.signals import new_friend_got_signal
from core.plunder import Plunder

import protomsg
from protomsg import FRIEND_NOT, FRIEND_OK, FRIEND_ACK, FRIEND_APPLY
from protomsg import Friend as MsgFriend

from preset.data import VIP_FUNCTION, VIP_MAX_LEVEL
from preset.settings import FRIEND_CANDIDATE_LEVEL_DIFF
from preset import errormsg
from utils import pack_msg


class Friend(object):
    def __init__(self, char_id):
        self.char_id = char_id
        self.char = Char(self.char_id)

        try:
            self.mf = MongoFriend.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mf = MongoFriend(id=self.char_id)
            self.mf.friends = []
            self.mf.pending = []
            self.mf.accepting = []

            self.mf.plunder_gives = []
            self.mf.plunder_gots = []
            self.mf.plunder_senders = []
            self.mf.save()

    def is_friend(self, target_id):
        # 真正的好友，对方接受了我的好友申请的
        return int(target_id) in self.mf.friends

    def is_general_friend(self, target_id):
        # 广义好友，只要是自己或者对方发过好友申请的都算
        target_id = int(target_id)
        return target_id in self.mf.friends or target_id in self.mf.pending or target_id in self.mf.accepting


    @property
    def max_amount(self):
        return VIP_FUNCTION[self.char.mc.vip].friends

    @property
    def cur_amount(self):
        return len(self.mf.friends) + len(self.mf.pending)

    @property
    def real_cur_amount(self):
        return len(self.mf.friends)


    def candidate_list(self, level_diff=FRIEND_CANDIDATE_LEVEL_DIFF):
        # 候选人列表
        level = self.char.mc.level
        char_ids = get_char_ids_by_level_range(level-level_diff, level+level_diff, exclude_char_ids=[self.char_id])

        res = []
        for c in char_ids:
            if self.is_general_friend(c):
                continue

            res.append(c)
            if len(res) >= 5:
                break

        return res


    def friends_list(self):
        """
        @return: All Friends List. Format: [(id, status), (id, status)...]
        @rtype: list
        """
        res = []
        for i in self.mf.friends:
            res.append((i, FRIEND_OK))

        for i in self.mf.pending:
            res.append((i, FRIEND_ACK))

        for i in self.mf.accepting:
            res.append((i, FRIEND_APPLY))

        return res

    def check_max_amount(self, func_name):
        if self.cur_amount >= self.max_amount:
            if self.char.mc.vip < VIP_MAX_LEVEL:
                raise SanguoException(
                    errormsg.FRIEND_FULL,
                    self.char_id,
                    func_name,
                    "friends full. vip current: {0}, max: {1}".format(self.char.mc.vip, VIP_MAX_LEVEL)
                )
            raise SanguoException(
                errormsg.FRIEND_FULL_FINAL,
                self.char_id,
                func_name,
                "friends full. vip reach max level {0}".format(VIP_MAX_LEVEL)
            )



    def add(self, target_id=None, target_name=None):
        # 发出好友申请
        if not target_id and not target_name:
            raise SanguoException(
                errormsg.BAD_MESSAGE,
                self.char_id,
                "Friend Add",
                "no target_id and no target_name"
            )

        self.check_max_amount("Friend Add")

        if target_id:
            try:
                c = MongoCharacter.objects.get(id=target_id)
            except DoesNotExist:
                raise SanguoException(
                    errormsg.CHARACTER_NOT_FOUND,
                    self.char_id,
                    "Friend Add",
                    "character id {0} not found".format(target_id)
                )
        else:
            try:
                c = MongoCharacter.objects.get(name=target_name)
            except DoesNotExist:
                raise SanguoException(
                    errormsg.CHARACTER_NOT_FOUND,
                    self.char_id,
                    "Friend Add",
                    u"can not found character {0} in server {1}".format(target_name, self.char.mc.server_id)
                )

        if c.id in self.mf.friends:
            raise SanguoException(
                errormsg.FRIEND_ALREADY_ADD,
                self.char_id,
                "Friend Add",
                "character {0} already has beed added".format(c.id)
            )

        if c.id in self.mf.pending:
            return

        if c.id in self.mf.accepting:
            # 如果要加的好友以前已经给我发过好友申请，那么就是直接接受
            self.accept(c.id)
            return

        self.mf.pending.append(c.id)
        self.mf.save()

        target_char_friend = Friend(c.id)
        target_char_friend.someone_add_me(self.char_id)

        # notify
        msg = protomsg.NewFriendNotify()
        self._msg_friend(msg.friend, c.id, FRIEND_ACK)
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def someone_add_me(self, from_id):
        from_id = int(from_id)
        if from_id in self.mf.accepting or from_id in self.mf.pending or from_id in self.mf.accepting:
            return

        self.mf.accepting.append(from_id)
        self.mf.save()

        msg = protomsg.NewFriendNotify()
        self._msg_friend(msg.friend, from_id, FRIEND_APPLY)
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def terminate(self, target_id):
        # 终止好友关系
        target_id = int(target_id)
        if target_id not in self.mf.friends:
            raise SanguoException(
                errormsg.FRIEND_NOT_OK,
                self.char_id,
                "Friend Terminate",
                "character {0} is not friend".format(target_id)
            )

        self.mf.friends.remove(target_id)
        self.mf.save()

        target_char_friend = Friend(target_id)
        target_char_friend.someone_terminate_me(self.char_id)

        msg = protomsg.RemoveFriendNotify()
        msg.id = target_id
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def someone_terminate_me(self, from_id):
        from_id = int(from_id)
        if from_id not in self.mf.friends:
            return

        self.mf.friends.remove(from_id)
        self.mf.save()

        msg = protomsg.RemoveFriendNotify()
        msg.id = from_id
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def cancel(self, target_id):
        # 取消好友申请
        target_id = int(target_id)
        if target_id not in self.mf.pending:
            raise SanguoException(
                errormsg.FRIEND_NOT_ACK,
                self.char_id,
                "Friend Cancel",
                "not ack for character {0}".format(target_id)
            )

        self.mf.pending.remove(target_id)
        self.mf.save()

        target_char_friend = Friend(target_id)
        target_char_friend.someone_cancel_me(self.char_id)

        msg = protomsg.RemoveFriendNotify()
        msg.id = target_id
        publish_to_char(self.char_id, pack_msg(msg))
        self.send_friends_amount_notify()

    def someone_cancel_me(self, from_id):
        if from_id not in self.mf.accepting:
            return

        self.mf.accepting.remove(from_id)
        self.mf.save()

        msg = protomsg.RemoveFriendNotify()
        msg.id = from_id
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def accept(self, target_id):
        # 接受对方的好友申请
        target_id = int(target_id)
        if target_id not in self.mf.accepting:
            raise SanguoException(
                errormsg.FRIEND_NOT_IN_ACCEPT_LIST,
                self.char_id,
                "Friend Accept",
                "character {0} not in accept list".format(target_id)
            )

        self.check_max_amount("Friend Accept")

        self.mf.accepting.remove(target_id)
        self.mf.friends.append(target_id)
        self.mf.save()

        target_char_friend = Friend(target_id)
        target_char_friend.someone_accept_me(self.char_id)

        self.send_update_friend_notify(target_id)

        new_friend_got_signal.send(
            sender=None,
            char_id=self.char_id,
            new_friend_id=target_id,
            total_friends_amount=self.real_cur_amount
        )

        self.send_friends_amount_notify()



    def someone_accept_me(self, from_id):
        from_id = int(from_id)
        if from_id in self.mf.pending:
            self.mf.pending.remove(from_id)
        if from_id not in self.mf.friends:
            self.mf.friends.append(from_id)
        self.mf.save()

        self.send_update_friend_notify(from_id)

        new_friend_got_signal.send(
            sender=None,
            char_id=self.char_id,
            new_friend_id=from_id,
            total_friends_amount=self.real_cur_amount
        )

        self.send_friends_amount_notify()


    def refuse(self, target_id):
        # 拒绝对方的好友申请
        target_id = int(target_id)
        if target_id not in self.mf.accepting:
            raise SanguoException(
                errormsg.FRIEND_NOT_IN_ACCEPT_LIST,
                self.char_id,
                "Friend Refuse",
                "character {0} not in accept list".format(target_id)
            )

        self.mf.accepting.remove(target_id)
        self.mf.save()

        target_char_friend = Friend(target_id)
        target_char_friend.someone_refuse_me(self.char_id)

        msg = protomsg.RemoveFriendNotify()
        msg.id = target_id
        publish_to_char(self.char_id, pack_msg(msg))
        self.send_friends_amount_notify()


    def someone_refuse_me(self, from_id):
        from_id = int(from_id)
        if from_id in self.mf.pending:
            self.mf.pending.remove(from_id)
        self.mf.save()

        msg = protomsg.RemoveFriendNotify()
        msg.id = from_id
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def _msg_friend(self, msg, fid, status):
        char_f = Char(fid)
        cache_f = char_f.cacheobj
        msg.id = fid
        msg.name = cache_f.name
        msg.level = cache_f.level
        msg.official = cache_f.official
        if status == FRIEND_OK or status == FRIEND_NOT:
            msg.power = char_f.power

        msg.status = status

        f = Formation(fid)
        in_formation_hero_ids = [h for h in f.in_formation_hero_ids() if h]
        hero_list = [(Hero.cache_obj(hid).power, hid) for hid in in_formation_hero_ids]
        hero_list.sort(key=lambda item: -item[0])
        leader_oid = Hero.cache_obj(hero_list[0][1]).oid

        if status == FRIEND_OK:
            f = Formation(fid)
            msg.formation.extend(f.in_formation_hero_original_ids())

        msg.leader = leader_oid

        if status == FRIEND_OK and fid not in self.mf.plunder_gives:
            msg.can_give_plunder_times = True
        else:
            msg.can_give_plunder_times = False

        if fid in self.mf.plunder_senders:
            msg.got_plunder_times_status = MsgFriend.CAN_GET
        elif fid in self.mf.plunder_gots:
            msg.got_plunder_times_status = MsgFriend.ALREADY_GET
        else:
            msg.got_plunder_times_status = MsgFriend.CAN_NOT_GET



    def send_friends_amount_notify(self):
        msg = protomsg.FriendsAmountNotify()
        msg.max_amount = self.max_amount
        msg.cur_amount = self.cur_amount
        publish_to_char(self.char_id, pack_msg(msg))


    def send_friends_notify(self):
        msg = protomsg.FriendsNotify()
        for k, v in self.friends_list():
            f = msg.friends.add()
            self._msg_friend(f, k, v)

        publish_to_char(self.char_id, pack_msg(msg))


    def send_update_friend_notify(self, friend_id, status=FRIEND_OK):
        msg = protomsg.UpdateFriendNotify()
        self._msg_friend(msg.friend, friend_id, status)
        publish_to_char(self.char_id, pack_msg(msg))


    # 行军令相关
    def give_plunder_times(self, target_id):
        target_id = int(target_id)
        if target_id not in self.mf.friends:
            raise SanguoException(
                errormsg.FRIEND_GIVE_PLUNDER_TIMES_NOT_FRIEND,
                self.char_id,
                "Friend Give Plunder Times",
                "{0} has no friend {1}".format(self.char_id, target_id)
            )

        if target_id in self.mf.plunder_gives:
            raise SanguoException(
                errormsg.FRIEND_GIVE_PLUNDER_TIMES_ALREADY_GIVE,
                self.char_id,
                "Friend Give Plunder Times",
                "{0} already give to {1}".format(self.char_id, target_id)
            )

        self.mf.plunder_gives.append(target_id)
        self.mf.save()

        self.send_update_friend_notify(target_id)

        f = Friend(target_id)
        f.someone_give_me_plunder_times(self.char_id)


    def someone_give_me_plunder_times(self, from_id):
        from_id = int(from_id)
        if from_id in self.mf.plunder_senders:
            return

        self.mf.plunder_senders.append(from_id)
        self.mf.save()

        self.send_update_friend_notify(from_id)

    def get_plunder_times(self, sender_id):
        if sender_id not in self.mf.plunder_senders:
            raise SanguoException(
                errormsg.FRIEND_GET_PLUNDER_TIMES_NOT_EXIST,
                self.char_id,
                "Friend Get Plunder Times",
                "{0} try to get plunder times, buy {1} not give".format(self.char_id, sender_id)
            )

        if sender_id in self.mf.plunder_gots:
            raise SanguoException(
                errormsg.FRIEND_GET_PLUNDER_TIMES_ALREADY_GOT,
                self.char_id,
                "Friend Get Plunder Times",
                "{0} try to get plunder times, buy already got from {1}".format(self.char_id, sender_id)
            )


        self.mf.plunder_senders.remove(sender_id)
        self.mf.plunder_gots.append(sender_id)
        self.mf.save()

        p = Plunder(self.char_id)
        p.change_current_plunder_times(change_value=1, allow_overflow=True)

        self.send_update_friend_notify(sender_id)


    def daily_plunder_times_reset(self):
        self.mf.plunder_gives = []
        self.mf.plunder_gots = []
        self.mf.save()
        self.send_friends_notify()
