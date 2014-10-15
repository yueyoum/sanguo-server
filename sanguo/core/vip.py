# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '5/26/14'

import copy

from mongoscheme import MongoCharacter
from core.msgpipe import publish_to_char
from core.attachment import get_drop, standard_drop_to_attachment_protomsg
from core.resource import Resource
from core.exception import SanguoException
from utils import pack_msg

from preset.data import VIP_DEFINE, VIP_REWARD
from preset import errormsg

from protomsg import VIPNotify


VIP_DEFINE_REVERSED = copy.deepcopy(VIP_DEFINE)
VIP_DEFINE_REVERSED.sort(reverse=True)

VIP_REWARD_IDS = VIP_REWARD.keys()
VIP_REWARD_IDS.sort()

def get_vip_level(total_purchase_got):
    for k, v in VIP_DEFINE_REVERSED:
        if total_purchase_got >= k:
            return v



class VIP(object):
    def __init__(self, char_id):
        self.char_id = char_id
        self.mc = MongoCharacter.objects.get(id=char_id)


    def can_reward_vips(self):
        vips = []
        for i in VIP_REWARD_IDS:
            if i > self.mc.vip:
                break

            if i not in self.mc.vip_has_reward:
                vips.append(i)

        return vips

    def get_reward(self, vip):
        if vip > self.mc.vip:
            raise SanguoException(
                errormsg.VIP_LEVEL_NOT_ENOUGH,
                self.char_id,
                "VIP GET REWARD",
                "vip not enough. {0} < {1}".format(self.mc.vip, vip)
            )

        vips = self.can_reward_vips()
        if vip not in vips:
            raise SanguoException(
                errormsg.VIP_HAS_GOT_REWARD,
                self.char_id,
                "VIP GET REWARD",
                "vip {0} has got reward".format(vip)
            )

        # send reward
        prepare_drop = get_drop([VIP_REWARD[vip].package])
        resource = Resource(self.char_id, "VIP GET REWARD", "vip {0}".format(vip))
        standard_drop = resource.add(**prepare_drop)

        self.mc.vip_has_reward.append(vip)
        self.mc.save()
        self.send_notify()

        return standard_drop_to_attachment_protomsg(standard_drop)


    def send_notify(self):
        msg = VIPNotify()
        msg.vip = self.mc.vip
        msg.reward_vips.extend(self.can_reward_vips())
        msg.purchase_got = self.mc.purchase_got
        publish_to_char(self.char_id, pack_msg(msg))
