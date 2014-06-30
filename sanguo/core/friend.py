# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '12/31/13'

from mongoengine import DoesNotExist

from core.mongoscheme import MongoFriend, MongoCharacter
from core.character import Char, get_char_ids_by_level_range
from core.hero import Hero
from core.msgpipe import publish_to_char
from core.exception import SanguoException
from core.achievement import Achievement
from core.formation import Formation

import protomsg
from protomsg import FRIEND_NOT, FRIEND_OK, FRIEND_ACK, FRIEND_APPLY

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
            self.mf.friends = {}
            self.mf.accepting = []
            self.mf.save()

    def is_friend(self, target_id):
        # 真正的好友，对方接受了我的好友申请的
        t = str(target_id)
        return t in self.mf.friends and self.mf.friends[t] == FRIEND_OK

    def is_general_friend(self, target_id):
        # 广义好友，只要是自己或者对方发过好友申请的都算
        return str(target_id) in self.mf.friends or target_id in self.mf.accepting


    @property
    def max_amount(self):
        return VIP_FUNCTION[self.char.mc.vip].friends

    @property
    def cur_amount(self):
        fs = self.mf.friends
        return len(fs)

    @property
    def real_cur_amount(self):
        fs = self.mf.friends.values()
        amount = 0
        for f in fs:
            if f == FRIEND_OK:
                amount += 1
        return amount


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
        fs = self.mf.friends
        for k, v in fs.iteritems():
            res.append((int(k), v))

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
                c = MongoCharacter.objects.get(name=target_name, server_id=self.char.mc.server_id)
            except DoesNotExist:
                raise SanguoException(
                    errormsg.CHARACTER_NOT_FOUND,
                    self.char_id,
                    "Friend Add",
                    u"can not found character {0} in server {1}".format(target_name, self.char.mc.server_id)
                )

        if str(c.id) in self.mf.friends:
            if self.mf.friends[str(c.id)] == FRIEND_OK:
                raise SanguoException(
                    errormsg.FRIEND_ALREADY_ADD,
                    self.char_id,
                    "Friend Add",
                    "character {0} already has beed added".format(c.id)
                )
            return

        self.mf.friends[str(c.id)] = FRIEND_ACK
        self.mf.save()

        target_char_friend = Friend(c.id)
        target_char_friend.someone_add_me(self.char_id)

        # notify
        msg = protomsg.NewFriendNotify()
        self._msg_friend(msg.friend, c.id, FRIEND_ACK)
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def someone_add_me(self, from_id):
        if from_id in self.mf.accepting or str(from_id) in self.mf.friends:
            return

        self.mf.accepting.append(from_id)
        self.mf.save()

        msg = protomsg.NewFriendNotify()
        self._msg_friend(msg.friend, from_id, FRIEND_APPLY)
        publish_to_char(self.char_id, pack_msg(msg))


    def terminate(self, target_id):
        t = str(target_id)
        if t not in self.mf.friends or self.mf.friends[t] != FRIEND_OK:
            raise SanguoException(
                errormsg.FRIEND_NOT_OK,
                self.char_id,
                "Friend Terminate",
                "character {0} is not friend".format(target_id)
            )

        self.mf.friends.pop(t)
        self.mf.save()

        target_char_friend = Friend(target_id)
        target_char_friend.someone_terminate_me(self.char_id)


        msg = protomsg.RemoveFriendNotify()
        msg.id = target_id
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def someone_terminate_me(self, from_id):
        t = str(from_id)
        if t not in self.mf.friends:
            return

        self.mf.friends.pop(t)
        self.mf.save()

        msg = protomsg.RemoveFriendNotify()
        msg.id = from_id
        publish_to_char(self.char_id, pack_msg(msg))

        self.send_friends_amount_notify()


    def cancel(self, target_id):
        t = str(target_id)
        if t not in self.mf.friends or self.mf.friends[t] != FRIEND_ACK:
            raise SanguoException(
                errormsg.FRIEND_NOT_ACK,
                self.char_id,
                "Friend Cancel",
                "not ack for character {0}".format(target_id)
            )

        self.mf.friends.pop(t)
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


    def accept(self, target_id):
        if target_id not in self.mf.accepting:
            raise SanguoException(
                errormsg.FRIEND_NOT_IN_ACCEPT_LIST,
                self.char_id,
                "Friend Accept",
                "character {0} not in accept list".format(target_id)
            )

        self.check_max_amount("Friend Accept")

        self.mf.accepting.remove(target_id)
        self.mf.friends[str(target_id)] = FRIEND_OK

        self.mf.save()

        target_char_friend = Friend(target_id)
        target_char_friend.someone_accept_me(self.char_id)

        msg = protomsg.UpdateFriendNotify()
        self._msg_friend(msg.friend, target_id, FRIEND_OK)
        publish_to_char(self.char_id, pack_msg(msg))


    def someone_accept_me(self, from_id):
        self.mf.friends[str(from_id)] = FRIEND_OK
        self.mf.save()

        achievement = Achievement(self.char_id)
        achievement.trig(27, self.real_cur_amount)

        msg = protomsg.UpdateFriendNotify()
        self._msg_friend(msg.friend, from_id, FRIEND_OK)
        publish_to_char(self.char_id, pack_msg(msg))


    def refuse(self, target_id):
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


    def someone_refuse_me(self, from_id):
        self.mf.friends.pop(str(from_id))
        self.mf.save()

        msg = protomsg.RemoveFriendNotify()
        msg.id = from_id
        publish_to_char(self.char_id, pack_msg(msg))


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
