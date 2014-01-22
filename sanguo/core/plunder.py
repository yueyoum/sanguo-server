# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '1/22/14'

from apps.character.models import Character
from core.character import Char
from core.battle import PVP

from core.exception import InvalidOperate

from protomsg import Battle as MsgBattle

class Plunder(object):
    def __init__(self, char_id):
        self.char_id = char_id


    def get_plunder_list(self):
        # FIXME 全场掠夺还是只掠夺挂机的

        # fake test
        import random
        charactes = Character.objects.values_list('id', flat=True)
        charactes = list(charactes)
        ids = []
        while True:
            if len(ids) >= 10 or not charactes:
                break

            c = random.choice(charactes)
            charactes.remove(c)
            if c not in ids:
                ids.append(c)

        res = []
        for i in ids:
            char = Char(i)
            res.append((i, char.cacheobj.name, 0, char.power))

        return res

    def plunder(self, _id):
        try:
            Character.objects.get(id=_id)
        except Character.DoesNotExist:
            raise InvalidOperate("NOT EXIST CHARACTER {0}".format(_id))

        msg = MsgBattle()
        pvp = PVP(self.char_id, _id, msg)
        pvp.start()
        return msg


