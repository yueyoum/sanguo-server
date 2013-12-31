# -*- coding: utf-8 -*-


__author__ = 'Wang Chao'
__date__ = '12/31/13'

from mongoengine import DoesNotExist

from apps.character.models import Character
from core.mongoscheme import MongoFriend
from core.character import Char
from core.msgpipe import publish_to_char
from core.exception import InvalidOperate, BadMessage, CharNotFound, SanguoViewException

import protomsg
from protomsg import FRIEND_NOT, FRIEND_OK, FRIEND_ACK, FRIEND_APPLY

from preset.settings import MAX_FRIENDS_AMOUNT
from utils import pack_msg


class Friend(object):
    def __init__(self, char_id):
        self.char_id = char_id
        self.char = Char(self.char_id)
        self.cache_char = self.char.cacheobj

        try:
            self.mf = MongoFriend.objects.get(id=self.char_id)
        except DoesNotExist:
            self.mf = MongoFriend(id=self.char_id)
            self.mf.save()

    def is_friend(self, target_id):
        t = str(target_id)
        return t in self.mf.friends and self.mf.friends[t] == FRIEND_OK

    def is_general_friend(self, target_id):
        return str(target_id) in self.mf.friends or target_id in self.mf.accepting


    @property
    def max_amount(self):
        # FIXME
        vip = 0
        return MAX_FRIENDS_AMOUNT

    @property
    def cur_amount(self):
        fs = self.mf.friends
        return len(fs)

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


    def add(self, target_id=None, target_name=None):
        if not target_id and not target_name:
            raise BadMessage("FriendAddResponse")

        if self.cur_amount >= self.max_amount:
            raise SanguoViewException(1001, "FriendAddResponse")

        if target_id:
            try:
                c = Character.objects.get(id=target_id)
            except Character.DoesNotExist:
                raise InvalidOperate("FriendAddResponse")
        else:
            try:
                c = Character.objects.get(server_id=self.cache_char.server_id, name=target_name)
            except Character.DoesNotExist:
                raise CharNotFound("FriendAddResponse")

        if str(c.id) in self.mf.friends:
            raise SanguoViewException(1000, "FriendAddResponse")

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
            raise InvalidOperate("FriendTerminateResponse")

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
            raise InvalidOperate("FriendCancelResponse")

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
            raise InvalidOperate("FriendAcceptResponse")

        if self.cur_amount > self.max_amount:
            raise SanguoViewException(1001, "FriendAcceptResponse")


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

        msg = protomsg.UpdateFriendNotify()
        self._msg_friend(msg.friend, from_id, FRIEND_OK)
        publish_to_char(self.char_id, pack_msg(msg))


    def refuse(self, target_id):
        if target_id not in self.mf.accepting:
            raise InvalidOperate("FriendRefuseResponse")

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
        if status == FRIEND_OK:
            msg.formation.extend(char_f.hero_oid_list)

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
