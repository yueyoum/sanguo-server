# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '5/26/14'


from preset.settings import VIP_FUNCTION_TABLE, VIP_DEFINE_TABLE

VIP_DEFINE_TUPLE = VIP_DEFINE_TABLE.items()
VIP_DEFINE_TUPLE.sort(reverse=True)


def get_vip_level(total_purchase_got):
    for k, v in VIP_DEFINE_TUPLE:
        if total_purchase_got >= k:
            return v

def get_vip_func_value(vip_level, func_name):
    return VIP_FUNCTION_TABLE[vip_level][func_name]
