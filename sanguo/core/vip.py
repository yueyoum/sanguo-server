# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '5/26/14'

import copy
from preset.data import VIP_DEFINE

VIP_DEFINE_REVERSED = copy.deepcopy(VIP_DEFINE)
VIP_DEFINE_REVERSED.sort(reverse=True)

def get_vip_level(total_purchase_got):
    for k, v in VIP_DEFINE_REVERSED:
        if total_purchase_got >= k:
            return v
