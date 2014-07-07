# -*- coding: utf-8 -*-

import core.drives
from mongoengine import *


class MongoFunctionOpen(Document):
    id = IntField(primary_key=True)
    # list of freeze func ids
    freeze = ListField(IntField())

    meta = {
        'collection': 'function_open',
    }


class MongoCharacter(Document):
    id = IntField(primary_key=True)
    account_id = IntField()
    server_id = IntField()

    name = StringField()
    gold = IntField(default=0)
    sycee = IntField(default=0)
    level = IntField(default=1)
    exp = IntField(default=0)
    official = IntField(default=0)
    official_exp = IntField(default=0)

    # 充值真实获得
    purchase_got = IntField(default=0)
    vip = IntField(default=0)

    meta = {
        'collection': 'character',
        'indexes': ['level', 'name'],
    }

MongoCharacter.ensure_indexes()


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
    hero = IntField(default=0)
    weapon = IntField(default=0)
    armor = IntField(default=0)
    jewelry = IntField(default=0)



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
    # 最大三星关卡
    max_star_stage = IntField()
    stage_new = IntField()
    # 开启的精英关卡, key 为关卡ID， value 为今日打的次数
    elites = DictField()
    # 精英关卡的星级，key 为关卡ID， value True表示三星
    elites_star = DictField()
    # 精英小关卡购买记录 key 为 ID, value 为购买次数
    elites_buy = DictField()
    # 开启的活动关卡
    activities = ListField(IntField())

    meta = {
        'collection': 'stage'
    }

class MongoEmbeddedHeroPanelHero(EmbeddedDocument):
    oid = IntField()
    # 是否是好卡
    good = BooleanField()
    opened = BooleanField()


class MongoHeroPanel(Document):
    id = IntField(primary_key=True)
    panel = MapField(EmbeddedDocumentField(MongoEmbeddedHeroPanelHero))
    # 上次刷新的时间戳
    last_refresh = IntField()

    meta = {
        'collection': 'heropanel'
    }



class MongoHero(Document):
    id = IntField(primary_key=True)
    char = IntField(required=True)
    oid = IntField(required=True)
    step = IntField(required=True)
    # 升阶是一点一点来的，而不是一下升上去的，progress记录了当前进度
    progress = IntField(required=True)

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



class MongoPlunder(Document):
    id = IntField(primary_key=True)
    points = IntField()
    # char key 为 char_id， value 为 boolean 表示是否是 玩家
    chars = DictField()

    # 记录下上次打赢的是谁，以便获取战俘
    target_char = IntField()
    # 记录下都领取过哪些类型的奖励，防止多次重复领取
    got_reward = ListField()

    meta = {
        'collection': 'plunder'
    }




class MongoEmbededPlunderLog(EmbeddedDocument):
    name = StringField()
    gold = IntField()



class MongoHang(Document):
    id = IntField(primary_key=True)
    # 当日已经用掉的时间
    used = IntField(default=0)

    meta = {
        'collection': 'hang',
    }


class MongoHangDoing(Document):
    id = IntField(primary_key=True)
    jobid = StringField()

    char_level = IntField()
    stage_id = IntField()
    # 开始的UTC 时间戳
    start = IntField()

    finished = BooleanField()
    # 实际挂机时间
    actual_seconds = IntField()

    # 被掠夺日志
    logs = ListField(EmbeddedDocumentField(MongoEmbededPlunderLog))

    plunder_win_times = IntField()
    plunder_lose_times = IntField()

    meta = {
        'collection': 'hang_doing',
        'indexes': ['char_level',]
    }

MongoHangDoing.ensure_indexes()




class MongoEmbededPrisoner(EmbeddedDocument):
    oid = IntField()
    prob = IntField()
    active = BooleanField(default=True)

    # 掠夺收益金币/2，这就是释放所得金币
    gold = IntField()

class MongoPrison(Document):
    id = IntField(primary_key=True)
    prisoners = MapField(EmbeddedDocumentField(MongoEmbededPrisoner))

    meta = {
        'collection': 'prison'
    }


class MongoCounter(Document):
    id = IntField(primary_key=True)
    # key 是 preset.settings.COUNTER 中的key，值表示已经进行了多少次
    counter = DictField()

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
    attachment = StringField(required=False)
    has_read = BooleanField(required=True)
    create_at = StringField(required=True)

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
    # 目前签到天数
    day = IntField()

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

    # 要显示的成就列表
    display = ListField()
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


class MongoArenaWeek(Document):
    id = IntField(primary_key=True)
    score = IntField(default=0)
    rank = IntField(default=0)
    # score 是每天的天积分累加的
    # rank 是上周的根据 score 的排名
    # 每天有定时任务把 天积分累加到这里的 score 上
    # 然后每周的定时任务会按照 这些score排名，并设置 rank,
    # 然后将score清空，最后把排名前三的设置到 TopRanks

    meta = {
        'collection': 'arena_week'
    }



class MongoAttachment(Document):
    id = IntField(primary_key=True)
    # prize_ids 保存当前所有可领取奖励的id号
    # attachments 如果保存有对应prize_id的 attachment，则直接在这里领取奖励
    # 否则就去对应的功能领取奖励
    prize_ids = ListField(IntField())
    attachments = DictField()

    meta = {
        'collection': 'attachment'
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
    self_power = IntField()
    start_at = IntField()
    total_seconds = IntField()
    # status: 2 started, 3 reward
    status = IntField()
    # 每秒进度，是否完成就看已经经过的秒数乘以这个数值是否达到1
    step = FloatField(default=0)
    friend_ids = ListField(IntField())

    meta = {
        'collection': 'teambattle'
    }

