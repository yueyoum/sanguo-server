# -*- coding: utf-8 -*-

#########################
#       初始化           #
#########################
#  角色
CHARACTER_INIT = {
    'gold': 0,          # 金币
    'sycee': 0,         # 元宝
    'hero_in_formation': {      # 在阵法中武将及其装备
        48: (8, 64, 78),        # 武将ID: (武器ID， 防具ID， 饰品ID). 装备一定要填满3个，没有的用0代替
        51: (22, 71, 92),
        74: (1, 71, 92),
    },
    'hero': [],          # [id,id...]   不在阵法中的武将
    'equipment': [],     # [(id,amount), (id,amount)...]
    'gem':[],            # [(id,amount), (id,amount)...]
    'stuff': [],         # [(id,amount), (id,amount)...]
    'souls': [],         # [(id,amount), (id,amount)...]
}

# 阵法  上面 `在阵法中武将的` 位置.
# 这两处的武将ID必须一一对应
FORMATION_INIT_TABLE = [
    0, 48, 0,            # 第一军
    0, 51, 0,            # 第二军
    0, 74, 0,            # 第三军
]

# 初始开启的阵法插槽
FORMATION_INIT_OPENED_SOCKETS = 4


#########################
#      奖励倍数          #
#########################
REWARD_GOLD_MULTIPLE = 1              # 得金币倍数
REWARD_SYCEE_MULTIPLE = 1             # 得元宝倍数
REWARD_EXP_MULTIPLE = 1               # 得经验倍数
REWARD_OFFICAL_EXP_MULTIPLE = 1       # 得官职经验倍数
REWARD_DROP_PROB_MULTIPLE = 1         # 掉率倍数



#########################
#      次数限制          #
#########################
# 每天可以做多少次
# 值为0的，是根据其他条件（比如VIP）具有不同值的。否则就是固定值
COUNTER = {
    'arena': 5,                         # 比武次数 免费
    'arena_buy': 0,                     # 比武次数 购买 VIP

    'plunder': 0,                       # 掠夺次数 VIP
    'gethero': 1,                       # 抽将次数
    'official_reward': 1,               # 官职每日登录领取奖励次数

    'stage_elite': 10,                  # 精英关卡总次数
    'stage_elite_buy_total': 0,         # 精英关卡总重置次数 VIP

    'levy': 0,                          # 征收次数 VIP
}
# 挂机时间是特殊处理的，所以不写在COUNTER里
# 其他一些和VIP相关的功能不是次数限制，所以也不在这里
# 活动关卡的总次数是用的 core.counter.ActivityStageCounter 来特殊处理的
# 是为了兼容以后再加新的活动关卡类型

# 精英关卡单个副本的重置次数是按照每个关卡单独计算的
# 所以将其放在 MongoStage 中记录

#########################
#      征收             #
#########################
# 征收暴击机率. (机率，暴击倍数). 机率以100为基准。1 表示1%的几率
LEVY_CRIT_PROB_TABLE = (
    (1, 10),
    (2, 5),
    (5, 3),
    (10, 2),
    (100, 1),
)
# 征收次数收费. （已经进行的次数，本次收费）
LEVY_COST_SYCEE = (
    (0, 0),
    (1, 10),
    (2, 20),
    (3, 20),
    (4, 20),
    (5, 20),
    (6, 40),
    (20, 80)
)
# 征收获得计算公式， 参数为 主公等级
LEVY_GOT_GOLD_FUNCTION = lambda level: 10000 + (level * 2)



#########################
#      关卡             #
#########################
# 关卡掉落概率基数
DROP_PROB_BASE = 100000


#########################
#      武将             #
#########################
# 武将最高阶数
HERO_MAX_STEP = 5
# 武将初始阶数
HERO_START_STEP = 0
# 武将升阶有几个孔
HERO_STEP_UP_SOCKET_AMOUNT = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}


#########################
#      抽将             #
#########################
# 抽奖，甲品质武将池
# 完整池 [1,10,11,12,13,14,15,16,17,18,19,2,20,21,22,23,24,25,26,27,28,29,3,30,31,32,33,34,35,36,37,38,39,4,43,44,5,56,6,7,8,83,9]
# 取出貂蝉、吕布
GET_HERO_QUALITY_ONE_POOL = [1,10,11,12,13,14,15,16,17,18,19,2,20,21,22,23,24,25,26,27,28,29,3,30,31,32,33,36,37,38,39,4,43,44,5,56,6,7,8,83,9]
# 抽奖，乙品质武将池
GET_HERO_QUALITY_TWO_POOL = [40,41,42,45,46,47,48,49,50,51,52,53,54,55,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,91]
# 抽奖，丙品质武将池
GET_HERO_QUALITY_THREE_POOL = [100,76,77,78,79,80,81,82,84,85,86,87,88,89,90,92,93,94,95,96,97,98,99]
# 抽奖多少几率产生两个甲品质卡 (基数为100)
GET_HERO_TWO_QUALITY_ONE_HEROS = 4
# 刷新间隔 （秒）
GET_HERO_REFRESH = 60 * 60 * 12
# 抽卡花费元宝
GET_HERO_COST = 300
# 抽卡强制刷新花费元宝 （刷新间隔还在冷却中）
GET_HERO_FORCE_REFRESH_COST = 100
# 抽卡得甲卡概率概率
# 抽的次数： 得甲卡概率
GET_HERO_QUALITY_ONE_PROB = {
    1: 1 * 2,
    2: 3 * 2,
    3: 6 * 2,
    4: 12 * 2,
    5: 30 * 1.5,
    6: 100,
}




#########################
#      装备             #
#########################
# 装备最高等级
EQUIP_MAX_LEVEL = 99
# 装备最高阶数 (初始第0阶)
EQUIP_MAX_STEP= 6


#########################
#      挂机             #
#########################




#########################
#      掠夺             #
#########################
# 掠夺失败获得官职经验
PLUNDER_GET_OFFICIAL_EXP_WHEN_LOST = 2
# 掠夺胜利获得官职经验
PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN = 5

# 掠夺点数（战功）  难度: {几星: 得多少分}
PLUNDER_GOT_POINT = {
    1: {2: 1, 3: 2},
    2: {2: 2, 3: 3},
    3: {2: 3, 3: 5},
}
# 防御成功获得金币
PLUNDER_DEFENSE_SUCCESS_GOLD = 1000
# 防御失败损失金币
PLUNDER_DEFENSE_FAILURE_GOLD = 1000
# 最大防御成功次数
PLUNDER_DEFENSE_SUCCESS_MAX_TIMES = 10
# 最大防御失败次数
PLUNDER_DEFENSE_FAILURE_MAX_TIMES = 10
# 掠夺获取收益各档所需点数
PLUNDER_REWARD_NEEDS_POINT = {1:3, 2: 2, 3: 1}
# 掠夺获取道具按照多少小时计算
PLUNDER_GOT_ITEMS_HOUR = 8

#########################
#      战俘             #
#########################
# 战俘初始劝降几率
PRISONER_START_PROB = 10
# 释放获得宝物 key: quality, value: 宝物ID列表
PRISONER_RELEASE_GOT_TREASURE = {3: [24], 2: [25], 1: [26]}
# 斩首获得宝物 key: quality, value: 宝物ID列表
PRISONER_KILL_GOT_TREASURE = {3: [24], 2: [25], 1: [26]}



#########################
#      比武             #
#########################
# 比武超过免费次数后每次比武消耗元宝
ARENA_COST_SYCEE = 20
# 比武胜利获得积分
ARENA_GET_SCORE_WHEN_WIN = 2
# 比武失败获得积分
ARENA_GET_SCORE_WHEN_LOST = 1


#########################
#      精英关卡         #
#########################
# 重置小关卡花费  (第几次重置， 花费)
STAGE_ELITE_RESET_COST = [
    (1, 20), (2, 50), (3, 50), (4, 100), (5, 100),
    (6, 100), (7, 200), (8, 200), (9, 300), (10, 300),
]
# 重置总次数花费   (第几次重置， 花费)
STAGE_ELITE_TOTAL_RESET_COST = [
    (1, 100), (2, 200), (3, 200), (4, 400)
]



#########################
#      攻击修正         #
#########################
# 1: 攻击型武将
# 2: 防御型武将
# 3: 策略
# 4: 君主
# 5: 其他
DEMAGE_VALUE_ADJUST = {
    1: {1: 0,     2: -0.05, 3: 0.05,  4: 0,     5: -0.05},
    2: {1: 0.05,  2: 0,     3: -0.05, 4: 0,     5: -0.05},
    3: {1: -0.05, 2: 0.05,  3: 0,     4: 0,     5: -0.05},
    4: {1: 0,     2: 0,     3: 0,     4: 0,     5: 0.05 },
    5: {1: 0,     2: 0,     3: 0,     4: -0.05, 5: 0    },
}



#########################
#      好友             #
#########################
FRIEND_CANDIDATE_LEVEL_DIFF = 10        # 好友候选人等级差


#########################
#      邮件             #
#########################
# 邮件可以保存多少天
MAIL_KEEP_DAYS = 7
# 激活码
ACTIVATECODE_MAIL_TITLE = u'激活码领取成功'
ACTIVATECODE_MAIL_CONTENT = u'激活码领取成功'
# 挂机
HANG_RESET_MAIL_TITLE = u'挂机清算补偿'
HANG_RESET_MAIL_CONTENT = u'挂机清算补偿'
# 比武日奖励
MAIL_ARENA_DAY_REWARD_TITLE = u'比武每日奖励'
MAIL_ARENA_DAY_REWARD_CONTENT = u'比武每日奖励'
# 比武周奖励
MAIL_ARENA_WEEK_REWARD_TITLE = u'比武每周奖励'
MAIL_ARENA_WEEK_REWARD_CONTENT = u'比武每周奖励'


#########################
#      激活码           #
#########################



#########################
#      聊天             #
#########################
CHAT_MESSAGE_MAX_LENGTH = 50            # 发送消息长度。多少个字



#########################
#      操作间隔时间 秒   #
#########################
OPERATE_INTERVAL_PVE = 5                # 普通关卡战斗间隔
OPERATE_INTERVAL_PVE_ELITE = 5          # 精英关卡战斗间隔
OPERATE_INTERVAL_PVE_ACTIVITY = 5       # 活动关卡间隔

OPERATE_INTERVAL_ARENA_PANEL = 5        # 竞技厂刷新面板间隔
OPERATE_INTERVAL_CHAT_SEND = 15         # 聊天发送间隔

OPERATE_INTERVAL_FRIEND_CANDIDATE_LIST = 5 # 添加好友的候选列表刷新间隔
OPERATE_INTERVAL_FRIEND_REFRESH = 5        # 刷新自己好友状态间隔

OPERATE_INTERVAL_PLUNDER_LIST = 5          # 获取掠夺列表间隔
OPERATE_INTERVAL_PLUNDER_BATTLE = 5        # 掠夺战斗间隔


#########################
#      其他             #
#########################

# 在线用户生存期
# 因为http协议不能记录登录用户，所以在用户最后一次操作后的生存期时间内，都认为此用户在线
# 应用场景：
#   1 发送聊天。只给在线用户发送
#   2 统计服务器压力
PLAYER_ON_LINE_TIME_TO_ALIVE = 60 * 60

# 服务器状态， (在线人数N，状态S)
# 状态对应关系 1 - 良好, 2 - 繁忙, 3 - 爆满, 4 - 维护
# 这里设置的就是 当在线人数超过N的时候，此服务器状态就是S。 要按照人数多少从多到少设置
SERVER_STATUS = ((1000, 3), (10, 2))
