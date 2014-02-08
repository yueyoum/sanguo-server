# -*- coding: utf-8 -*-

from mongoengine import *
import core.drives


class MongoEmbeddedEquipment(EmbeddedDocument):
    oid = IntField()
    level = IntField()
    gems = ListField(IntField())


class MongoItem(Document):
    id = IntField(primary_key=True)
    # 装备
    equipments = MapField(EmbeddedDocumentField(MongoEmbeddedEquipment))
    # 宝石
    gems = DictField()
    # 材料
    stuffs = DictField()

    meta = {
        'collection': 'item'
    }


class MongoSocket(EmbeddedDocument):
    # 阵法插槽
    hero = IntField()
    weapon = IntField()
    armor = IntField()
    jewelry = IntField()



class MongoFormation(Document):
    id = IntField(primary_key=True)
    sockets = MapField(EmbeddedDocumentField(MongoSocket))
    formation = ListField(IntField())

    meta = {
        'collection': 'formation'
    }

class MongoStage(Document):
    id = IntField(primary_key=True)
    # 已经打过的关卡，key为关卡ID，value 为 bool 值表示是否三星
    stages = DictField()
    stage_new = IntField()

    meta = {
        'collection': 'stage'
    }

class MongoHeroPanel(Document):
    id = IntField(primary_key=True)
    # 甲品质卡
    good_hero = IntField()
    # 其他卡，（可能包括一张甲卡）
    other_heros = ListField(IntField())
    panel = DictField()
    # 这组卡牌是否开始
    started = BooleanField()
    # 上次刷新的时间戳
    last_refresh = IntField()

    meta = {
        'collection': 'heropanel'
    }



class MongoHero(Document):
    id = IntField(primary_key=True)
    char = IntField(required=True)
    oid = IntField(required=True)
    step = IntField(required=True, default=1)

    meta = {
        'collection': 'hero',
        'indexes': ['char', ]
    }


MongoHero.ensure_indexes()


class MongoHang(Document):
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


MongoHang.ensure_indexes()


class MongoEmbededPrisoner(EmbeddedDocument):
    id = IntField()
    oid = IntField()
    start_time = IntField()
    status = IntField()
    jobid = StringField()


class MongoPrison(Document):
    id = IntField(primary_key=True)
    amount = IntField()
    prisoners = MapField(EmbeddedDocumentField(MongoEmbededPrisoner))

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


class MongoEmbededMail(EmbeddedDocument):
    name = StringField(required=True)
    content = StringField(required=True)
    attachment = BinaryField()
    has_read = BooleanField(required=True)
    # utc timestamp
    create_at = IntField(required=True)

class MongoMail(Document):
    id = IntField(primary_key=True)
    mails = MapField(EmbeddedDocumentField(MongoEmbededMail))

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


class MongoTask(Document):
    id = IntField(primary_key=True)
    # key 为任务类型ID， value为此类型次数
    tasks = DictField()
    # 已领取奖励的任务ID列表（彻底完成）
    complete = ListField()
    # 已经完成但还没领取奖励的ID列表
    finished = ListField()
    # 当前进行的任务ID列表 （包括没完成的，完成的但还没领奖的，每种任务类型的最后一档任务）
    doing = ListField()

    meta = {
        'collection': 'task'
    }

