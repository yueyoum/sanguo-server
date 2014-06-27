# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-25'


from core.mongoscheme import MongoHangDoing, MongoFunctionOpen


def not_hang_going(char_id):
    return MongoHangDoing.objects.filter(id=char_id).count() == 0

def func_opened(char_id, func_id):
    fo = MongoFunctionOpen.objects.get(id=char_id)
    return func_id not in fo.freeze
