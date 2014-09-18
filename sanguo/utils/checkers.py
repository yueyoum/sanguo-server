# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-6-25'


from mongoengine import DoesNotExist
from core.mongoscheme import MongoFunctionOpen, MongoAffairs


def not_hang_going(char_id):
    try:
        affairs = MongoAffairs.objects.get(id=char_id)
    except DoesNotExist:
        return True

    return affairs.hang_city_id == 0

def func_opened(char_id, func_id):
    fo = MongoFunctionOpen.objects.get(id=char_id)
    return func_id not in fo.freeze
