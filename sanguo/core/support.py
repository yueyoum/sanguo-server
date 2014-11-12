# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '14-11-12'

import cPickle
from cPickle import HIGHEST_PROTOCOL

from mongoengine import DoesNotExist
from core.mongoscheme import MongoRedisPersistence

def dumps(data):
    return cPickle.dumps(data, HIGHEST_PROTOCOL)

def loads(data):
    return cPickle.loads(data)


class RedisPersistence(object):
    MONGOID = None
    REDISKEY = None

    @classmethod
    def get_subclasses(cls):
        # FIX ME
        # DO THIS AUTOMIC
        from core.arena import ArenaScoreBoard
        from core.plunder import PlunderLeaderboardWeekly
        return [ArenaScoreBoard, PlunderLeaderboardWeekly,]

    @classmethod
    def all_dumps(cls):
        for C in cls.get_subclasses():
            C.obj_dumps()

    @classmethod
    def all_loads(cls):
        for C in cls.get_subclasses():
            C.obj_loads()

    @classmethod
    def obj_dumps(cls):
        data = cls.get_data_from_redis()
        cls.save_data_into_mongodb(data)


    @classmethod
    def obj_loads(cls):
        data = cls.get_data_from_mongodb()
        cls.save_data_into_redis(data)


    @classmethod
    def get_data_from_redis(cls):
        raise NotImplementedError()

    @classmethod
    def save_data_into_redis(cls, data):
        raise NotImplementedError()

    @classmethod
    def get_data_from_mongodb(cls):
        try:
            mrp = MongoRedisPersistence.objects.get(id=cls.MONGOID)
            return loads(mrp.data)
        except DoesNotExist:
            return None

    @classmethod
    def save_data_into_mongodb(cls, data):
        data = dumps(data)
        try:
            mrp = MongoRedisPersistence.objects.get(id=cls.MONGOID)
        except DoesNotExist:
            mrp = MongoRedisPersistence(id=cls.MONGOID)

        mrp.data = data
        mrp.save()


