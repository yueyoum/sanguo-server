# -*- coding: utf-8 -*-

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# 次数限制，每天可以做多少次
COUNTER = {
    'arena': 5,          # 比武次数 免费
    'arena_sycee': 5,    # 比武次数 购买
    'plunder': 10,        # 掠夺次数 免费
    'gethero': 1,        # 免费抽将次数
    'official_reward': 1,       # 官职每日登录领取奖励次数

    'stage_elite': 3,                   # 精英关卡总次数
    'stage_active_type_one': 3,         # 活动产金币关卡总次数
    'stage_active_type_two': 3,         # 活动产宝石宝物关卡总次数
}

#########################
#      关卡             #
#########################
# 每日挂机时间
HANG_SECONDS = 16 * 3600
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
#      装备             #
#########################
# 装备最高等级
EQUIP_MAX_LEVEL = 99
# 装备最高阶数 (初始第0阶)
EQUIP_MAX_STEP= 6


#########################
#      挂机             #
#########################

HANG_RESET_MAIL_TITLE = u'挂机清算补偿'
HANG_RESET_MAIL_CONTENT = u'挂机清算补偿'


#########################
#      掠夺             #
#########################
# 掠夺失败获得官职经验
PLUNDER_GET_OFFICIAL_EXP_WHEN_LOST = 2
# 掠夺胜利获得官职经验
PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN = 5
# 掠夺点数（战功）
PLUNDER_POINT = {2: 1, 3: 2}
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
PLUNDER_GOT_ITEMS_HOUR = 2

#########################
#      战俘             #
#########################
# 战俘初始劝降几率
PRISONER_START_PROB = 10
# 释放获得宝物 key: quality, value: 宝物ID列表
PRISONER_RELEASE_GOT_TREASURE = {3: [24], 2: [25], 1: [26]}
# 斩首获得宝物 key: quality, value: 宝物ID列表
PRISONER_KILL_GOT_TREASURE = {3: [24], 2: [25], 1: [26]}
# 斩首获得通用卡魂 key: quality, value: amount
PRISONER_KILL_GOT_SOUL = {3: 1, 2: 2, 1: 3}


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
#      攻击修正          #
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
# 基本好友最大数量
MAX_FRIENDS_AMOUNT = 25

# 邮件可以保存多少天
MAIL_KEEP_DAYS = 7

# 猛将挑战增加一分钟需要多少元宝
TEAMBATTLE_INCR_COST = 100
