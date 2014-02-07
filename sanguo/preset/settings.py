# -*- coding: utf-8 -*-


# 创建角色的初始化数据
CHAR_INITIALIZE = {
    'gold': 0, # 金币
    'sycee': 0, # 元宝
    'level': 1, # 等级
    'official': 1, # 官职

    'heros': [1, 2, 3], # 要给的英雄，不设置为随机3个
    # 装备到英雄身上的装备
    'equips_on': {
        1: [],
        2: [],
        3: [],
    },
    'equips': [(1, 3), (78, 3), (102, 3)], # 要给的装备，格式为 [(id, amount), (id amount)...]
    'gems': [], # 要给的宝石，格式为 [(gid, amount), (gid, amount)...]
}




# 次数限制，每天可以做多少次
# 每天可以做多少次
COUNTER = {
    'hang': 8, # 挂机时间
    'arena': 8, # 比武次数
    'plunder': 8,        # 掠夺次数
    'gethero': 1,        # 免费抽将次数
}


# 战俘最多可以有多少个
MAX_PRISONERS_AMOUNT = 10
# 掠夺消耗元宝
PLUNDER_COST_SYCEE = 1

# 最大训练位数量
MAX_PRISON_TRAIN_SLOT = 3
# 开启训练位花费元宝
COST_OPEN_PRISON_SLOT = 1


# 基本好友最大数量
MAX_FRIENDS_AMOUNT = 5

# 邮件可以保存多少天
MAIL_KEEP_DAYS = 1