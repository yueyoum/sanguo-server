# -*- coding: utf-8 -*-

from mongoengine import *
import core.drives


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


class Hang(Document):
    id = IntField(primary_key=True)
    stage_id = IntField()
    # 选择的总时间
    hours = IntField()
    # 开始的UTC 时间戳
    start = IntField()
    # 是否完成
    finished = BooleanField()
    # 实际挂的时间
    actual_hours = IntField()
    jobid = StringField()

    meta = {
        'collection': 'hang',
        'indexes': ['stage_id', ]
    }


Hang.ensure_indexes()


class Prisoner(EmbeddedDocument):
    id = IntField()
    oid = IntField()
    start_time = IntField()
    status = IntField()
    jobid = StringField()


class MongoPrison(Document):
    id = IntField(primary_key=True)
    amount = IntField()
    prisoners = MapField(EmbeddedDocumentField(Prisoner))

    meta = {
        'collection': 'prison'
    }


class MongoCounter(Document):
    id = StringField(primary_key=True)
    cur_value = IntField()

    meta = {
        'collection': 'counter'
    }


class MongoFriend(Document):
    id = IntField(primary_key=True)
    # 已加好友和自己发出的申请
    friends = DictField()
    # 别人发来的申请需要我接受的
    accepting = ListField(IntField())

    meta = {
        'collection': 'friend'
    }


class EmbededMail(EmbeddedDocument):
    name = StringField(required=True)
    content = StringField(required=True)
    attachment = BinaryField()
    has_read = BooleanField(required=True)
    # utc timestamp
    create_at = IntField(required=True)

class MongoMail(Document):
    id = IntField(primary_key=True)
    mails = MapField(EmbeddedDocumentField(EmbededMail))

    meta = {
        'collection': 'mail'
    }


class MongoCheckIn(Document):
    id = IntField(primary_key=True)
    days = ListField(IntField())
    has_get = ListField(IntField())

    meta = {
        'collection': 'checkin'
    }
