# -*- coding: utf-8 -*-

from mongoengine import *
import core.drives

from protomsg import Attachment as MsgAttachment


class MongoChar(Document):
    id = IntField(primary_key=True)
    got_gold = IntField(default=0)
    got_sycee = IntField(default=0)
    cost_gold = IntField(default=0)
    cost_sycee = IntField(default=0)

    meta = {
        'collection': 'char'
    }


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
    # 开启的精英关卡, key 为关卡ID， value 为今日打的次数
    elites = DictField()

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



class MongoHeroSoul(Document):
    id = IntField(primary_key=True)
    # key 为将魂ID， value 为数量
    souls = DictField()

    meta = {
        'collection': 'hero_soul',
    }


class MongoEmbededPlunderChar(EmbeddedDocument):
    is_robot = BooleanField()
    gold = IntField()

class MongoPlunderList(Document):
    id = IntField(primary_key=True)
    chars = MapField(EmbeddedDocumentField(MongoEmbededPlunderChar))

    meta = {
        'collection': 'plunderlist'
    }



class MongoEmbededPlunderLog(EmbeddedDocument):
    name = StringField()
    gold = IntField()


class MongoHang(Document):
    id = IntField(primary_key=True)
    char_level = IntField()
    stage_id = IntField()
    # 开始的UTC 时间戳
    start = IntField()
    # 是否完成
    finished = BooleanField()
    # 实际挂的时间
    actual_seconds = IntField()
    # jobid = StringField()

    # 被掠夺日志
    logs = ListField(EmbeddedDocumentField(MongoEmbededPlunderLog))
    # 被掠夺获得/损失金币
    plunder_gold = IntField()
    # 上次被掠夺的时间戳
    plunder_time = IntField()

    meta = {
        'collection': 'hang',
        'indexes': ['char_level',]
    }


MongoHang.ensure_indexes()


class MongoEmbededPrisoner(EmbeddedDocument):
    oid = IntField()
    prob = IntField()

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
    create_at = DateTimeField(required=True)

class MongoMail(Document):
    id = IntField(primary_key=True)
    mails = MapField(EmbeddedDocumentField(MongoEmbededMail))

    meta = {
        'collection': 'mail'
    }


class MongoCheckIn(Document):
    id = IntField(primary_key=True)
    # 当天是否已经签过。 次标志用定时任务修改
    has_checked = BooleanField()
    # 总共签到天数。到最大循环天数后归零
    days = IntField()

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


class MongoAchievement(Document):
    id = IntField(primary_key=True)
    # 当前开始进行的，但还没完成
    # key 为成就ID， value 为值 （不一定是Int）
    doing = DictField()
    # 已完成但还没领奖的
    finished = ListField()
    # 彻底完成的
    complete = ListField()

    meta = {
        'collection': 'achievement'
    }


class MongoArenaTopRanks(Document):
    # 排名前三的
    id = IntField(primary_key=True)
    name = StringField()

    meta = {
        'collection': 'arena_top_ranks'
    }


class MongoEmbededAttachmentEquipment(EmbeddedDocument):
    id = IntField()
    level = IntField(default=1)
    step = IntField(default=1)
    amount = IntField(default=1)

class MongoEmbededAttachment(EmbeddedDocument):
    equipments = ListField(EmbeddedDocumentField(MongoEmbededAttachmentEquipment))
    gems = DictField()
    stuffs = DictField()
    gold = IntField(default=0)
    sycee = IntField(default=0)
    exp = IntField(default=0)
    official_exp = IntField(default=0)
    heros = ListField(IntField())

    def to_protobuf(self):
        msg = MsgAttachment()
        if self.gold:
            msg.gold = self.gold
        if self.sycee:
            msg.sycee = self.sycee
        if self.official_exp:
            msg.official_exp = self.official_exp
        if self.heros:
            msg.heros.extend(self.heros)

        for item in self.equipments:
            e = msg.equipments.add()
            e.id = item.id
            e.level = item.level
            e.step = item.step
            e.amount = item.amount

        for k, v in self.gems:
            g = msg.gems.add()
            g.id = int(k)
            g.amount = v

        for k, v in self.stuffs:
            s = msg.stuffs.add()
            s.id = int(k)
            s.amount = v

        return msg



class MongoAttachment(Document):
    id = IntField(primary_key=True)
    # prize_ids 保存当前所有可领取奖励的id号
    # attachments 如果保存有对应prize_id的 attachment，则直接在这里领取奖励
    # 否则就去对应的功能领取奖励
    prize_ids = ListField(IntField())
    attachments = MapField(EmbeddedDocumentField(MongoEmbededAttachment))

    meta = {
        'collection': 'attachment'
    }


class MongoStoreAmount(Document):
    id = IntField(primary_key=True)
    sold_amount = IntField(default=0)

    # 有总量的物品的卖出数量，id为商品id，sold_amount为卖出数量
    meta = {
        'collection': 'store_amount'
    }


class MongoStoreCharLimit(Document):
    id = IntField(primary_key=True)
    # 每人每天限量购买记录
    # 已经买过的商品，key 为id， values 为已经买的量
    limits = DictField()

    meta = {
        'collection': 'store_char'
    }


class MongoTeamBattle(Document):
    id = IntField(primary_key=True)
    battle_id = IntField()
    boss_id = IntField()
    boss_power = IntField()
    friend_ids = ListField(IntField())
    self_power = IntField()
    start_at = IntField()
    total_seconds = IntField()
    # status: 1 prepare, 2 started, 3 reward
    status = IntField()

    meta = {
        'collection': 'teambattle'
    }
