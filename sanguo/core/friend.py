# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '12/31/13'

import random
from mongoengine import DoesNotExist

from core.mongoscheme import MongoFriend, MongoCharacter
from core.character import Char, get_char_ids_by_level_range
from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.signals import new_friend_got_signal
from core.plunder import Plunder
from core.activeplayers import ActivePlayers
from core.mail import Mail
from core.msgfactory import create_character_infomation_message

import protomsg
from protomsg import FRIEND_NOT, FRIEND_OK, FRIEND_ACK, FRIEND_APPLY
from protomsg import Friend as MsgFriend

from preset.data import VIP_FUNCTION, VIP_MAX_LEVEL
from preset.settings import (
    FRIEND_CANDIDATE_LEVEL_DIFF,
    FRIEND_CANDIDATE_LIST_AMOUNT,
    MAIL_FRIEND_REFUSE_TITLE,
    MAIL_FRIEND_REFUSE_CONTENT,
)

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

        # 先从最近活跃用户找，如果没有再通找
        ap = ActivePlayers()
        ap_list = ap.get_list()

        random.shuffle(ap_list)

        char_ids = []
        for c in ap_list:
            if c == self.char_id:
                continue
            if self.is_general_friend(c):
                continue

            char_ids.append(c)
            if len(char_ids) >= FRIEND_CANDIDATE_LIST_AMOUNT:
                break

        if len(char_ids) >= FRIEND_CANDIDATE_LIST_AMOUNT:
            return char_ids


        # 数量不够，补充
        level = self.char.mc.level
        supply_char_ids = get_char_ids_by_level_range(level-level_diff, level+level_diff, exclude_char_ids=[self.char_id])

        for c in supply_char_ids:
            if self.is_general_friend(c):
                continue

            if c in char_ids:
                continue

            char_ids.append(c)
            if len(char_ids) >= FRIEND_CANDIDATE_LIST_AMOUNT:
                break

        return char_ids


    def friends_list(self):
        """
        @return: All Friends List. Format: [(id, status), (id, status)...]
        @rtype: list
        """
        res = []
        for i in self.mf.friends[:]:
            # try:
            #     MongoCharacter.objects.get(id=i)
            # except DoesNotExist:
            #     self.mf.friends.remove(i)
            # else:
            #     res.append((i, FRIEND_OK))
            res.append((i, FRIEND_OK))

        for i in self.mf.pending[:]:
            # try:
            #     MongoCharacter.objects.get(id=i)
            # except DoesNotExist:
            #     self.mf.pending.remove(i)
            # else:
            #     res.append((i, FRIEND_ACK))
            res.append((i, FRIEND_ACK))

        for i in self.mf.accepting[:]:
            # try:
            #     MongoCharacter.objects.get(id=i)
            # except DoesNotExist:
            #     self.mf.accepting.remove(i)
            # else:
            #     res.append((i, FRIEND_APPLY))
            res.append((i, FRIEND_APPLY))

        # self.mf.save()
        return res

    def check_max_amount(self, func_name, raise_exception=True):
        if raise_exception:
            if self.real_cur_amount >= self.max_amount:
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
        else:
            if self.real_cur_amount >= self.max_amount:
                return False
            return True



    def add(self, target_id=None, target_name=None):
        # 发出好友申请
        if not target_id and not target_name:
            raise SanguoException(
                errormsg.BAD_MESSAGE,
                self.char_id,
                "Friend Add",
                "no target_id and no target_name"
            )

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

        self.check_max_amount("Friend Add")

        if c.id in self.mf.accepting:
            # 如果要加的好友以前已经给我发过好友申请，那么就是直接接受
            self.accept(c.id)
            return

        if c.id not in self.mf.pending:
            self.mf.pending.append(c.id)
            self.send_new_friend_notify(c.id, status=FRIEND_ACK)

        self.mf.save()

        target_char_friend = Friend(c.id)
        target_char_friend.someone_add_me(self.char_id)



    def someone_add_me(self, from_id):
        from_id = int(from_id)
        if from_id in self.mf.friends or from_id in self.mf.accepting:
            return

        self.mf.accepting.append(from_id)
        self.mf.save()

        if from_id in self.mf.pending:
            # 对方要加我，但我也给要加对方，那就直接成为好友
            self.accept(from_id)
            return

        self.send_new_friend_notify(from_id, status=FRIEND_APPLY)


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

        self.send_remove_friend_notify([target_id])
        self.send_friends_amount_notify()


    def someone_terminate_me(self, from_id):
        from_id = int(from_id)
        if from_id not in self.mf.friends:
            return

        self.mf.friends.remove(from_id)
        self.mf.save()

        self.send_remove_friend_notify([from_id])
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

        self.send_remove_friend_notify([target_id])
        # self.send_friends_amount_notify()

    def someone_cancel_me(self, from_id):
        if from_id not in self.mf.accepting:
            return

        self.mf.accepting.remove(from_id)
        self.mf.save()

        self.send_remove_friend_notify([from_id])
        # self.send_friends_amount_notify()


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


        def _clean_target_pending(target_id):
            target = Friend(target_id)
            if self.char_id in target.mf.pending:
                target.mf.pending.remove(self.char_id)
                target.mf.save()
                target.send_remove_friend_notify([self.char_id])

        target_char_friend = Friend(target_id)

        # 检查对方好友是否已满
        if not target_char_friend.check_max_amount("Friend Accept By Other", raise_exception=False):
            # 对方满了
            # 并且删除此人的申请
            self.mf.accepting.remove(target_id)
            self.mf.save()
            self.send_remove_friend_notify([target_id])

            _clean_target_pending(target_id)

            raise SanguoException(
                errormsg.FRIEND_OTHER_SIDE_IS_FULL,
                self.char_id,
                "Friend Accept",
                "other side {0} firend is full".format(target_id)
            )


        # 然后检查自己好友是否已满
        try:
            self.check_max_amount("Friend Accept")
        except SanguoException as e:
            # 满了就清空所有申请
            self.send_remove_friend_notify(self.mf.accepting)
            _accepting = self.mf.accepting
            self.mf.accepting = []
            self.mf.save()

            for _acc in _accepting:
                _clean_target_pending(_acc)
            raise e

        self.mf.accepting.remove(target_id)
        self.mf.friends.append(target_id)
        self.mf.save()

        target_char_friend = Friend(target_id)
        target_char_friend.someone_accept_me(self.char_id)


        new_friend_got_signal.send(
            sender=None,
            char_id=self.char_id,
            new_friend_id=target_id,
            total_friends_amount=self.real_cur_amount
        )

        self.send_update_friend_notify(target_id)
        self.send_friends_amount_notify()



    def someone_accept_me(self, from_id):
        from_id = int(from_id)
        if from_id in self.mf.pending:
            self.mf.pending.remove(from_id)
        if from_id not in self.mf.friends:
            self.mf.friends.append(from_id)
        self.mf.save()

        self.send_new_friend_notify(from_id)

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

        self.send_remove_friend_notify([target_id])
        self.send_friends_amount_notify()


    def someone_refuse_me(self, from_id):
        from_id = int(from_id)
        if from_id in self.mf.pending:
            self.mf.pending.remove(from_id)
        self.mf.save()

        from_char = Char(from_id)

        mail = Mail(self.char_id)
        mail.add(
            MAIL_FRIEND_REFUSE_TITLE,
            MAIL_FRIEND_REFUSE_CONTENT.format(from_char.mc.name)
        )

        self.send_remove_friend_notify([from_id])
        self.send_friends_amount_notify()


    def _msg_friend(self, msg, fid, status):
        msg.char.MergeFrom(create_character_infomation_message(fid))
        msg.status = status

        if status == FRIEND_OK and fid not in self.mf.plunder_gives:
            msg.can_give_plunder_times = True
        else:
            msg.can_give_plunder_times = False


        if status != FRIEND_OK:
            msg.got_plunder_times_status = MsgFriend.CAN_NOT_GET
        else:
            if fid in self.mf.plunder_senders:
                msg.got_plunder_times_status = MsgFriend.CAN_GET
            elif fid in self.mf.plunder_gots:
                msg.got_plunder_times_status = MsgFriend.ALREADY_GET
            else:
                msg.got_plunder_times_status = MsgFriend.CAN_NOT_GET



    def send_friends_amount_notify(self):
        msg = protomsg.FriendsAmountNotify()
        msg.max_amount = self.max_amount
        msg.cur_amount = self.real_cur_amount
        publish_to_char(self.char_id, pack_msg(msg))


    def send_friends_notify(self):
        msg = protomsg.FriendsNotify()
        for k, v in self.friends_list():
            f = msg.friends.add()
            self._msg_friend(f, k, v)

        publish_to_char(self.char_id, pack_msg(msg))


    def send_new_friend_notify(self, friend_id, status=FRIEND_OK):
        msg = protomsg.NewFriendNotify()
        self._msg_friend(msg.friend, friend_id, status)
        publish_to_char(self.char_id, pack_msg(msg))

    def send_update_friend_notify(self, friend_id, status=FRIEND_OK):
        msg = protomsg.UpdateFriendNotify()
        self._msg_friend(msg.friend, friend_id, status)
        publish_to_char(self.char_id, pack_msg(msg))

    def send_remove_friend_notify(self, friend_ids):
        for i in friend_ids:
            msg = protomsg.RemoveFriendNotify()
            msg.id = i
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

        if len(self.mf.plunder_gots) >= self.max_amount:
            raise SanguoException(
                errormsg.PLUNDER_GET_TIMES_FULL,
                self.char_id,
                "Friend Get Plunder Times",
                "{0} try to get plunder times, buy already reach max friends amount".format(self.char_id)
            )


        self.mf.plunder_senders.remove(sender_id)
        self.mf.plunder_gots.append(sender_id)
        self.mf.save()

        p = Plunder(self.char_id)
        p.change_current_plunder_times(change_value=1, allow_overflow=True)

        self.send_update_friend_notify(sender_id)


    @staticmethod
    def cron_job():
        condition = {"$or": [
            {"plunder_gives.0": {"$exists": True}},
            {"plunder_gots.0": {"$exists": True}}
        ]}

        friends = MongoFriend._get_collection().find(condition, {'_id': 1})

        updater = {
            'plunder_gives': [],
            'plunder_gots': []
        }

        MongoFriend._get_collection().update({}, {'$set': updater}, multi=True)

        for f in friends:
            Friend(f['_id']).send_friends_notify()

    # def daily_plunder_times_reset(self):
    #     self.mf.plunder_gives = []
    #     self.mf.plunder_gots = []
    #     # self.mf.save()
    #     self.send_friends_notify()
