# -*- coding: utf-8 -*-

from mongoengine import *

class MongoSocket(EmbeddedDocument):
    # 阵法插槽
    hero = IntField()
    weapon = IntField()
    armor = IntField()
    jewelry = IntField()
    

class MongoChar(Document):
    id = IntField(primary_key=True)
    
    # 插槽信息
    sockets = MapField(EmbeddedDocumentField(MongoSocket))
    # 阵法列表，按顺序保存插槽id
    formation = ListField(IntField())
    # 已经打过的关卡，key为关卡ID，value 为 bool 值表示是否三星
    stages = DictField()
    # 新的可以打的关卡
    stage_new = IntField()
    
    # 装备列表
    # 装备存储在mysql中，使用post, delete信号来更新这里的数据
    equips = ListField(IntField())
    
    # 宝石, key 为宝石ID， value为数量
    gems = DictField()
    
    meta = {
        'collection': 'char'
    }

class MongoHero(Document):
    id = IntField(primary_key=True)
    char = IntField(required=True)
    oid = IntField(required=True)
    
    meta = {
        'collection': 'hero',
        'indexes': ['char', ]
    }

MongoHero.ensure_indexes()


