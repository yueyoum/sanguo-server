# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-25'


from core.mongoscheme import MongoHangDoing


def not_hang_going(char_id):
    return MongoHangDoing.objects.filter(id=char_id).count() == 0
