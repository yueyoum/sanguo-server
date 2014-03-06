# -*- coding: utf-8 -*-



# 次数限制，每天可以做多少次
COUNTER = {
    'hang': 8 * 3600,    # 挂机时间
    'arena': 5,          # 比武次数 免费
    'plunder': 5,        # 掠夺次数 免费
    'arena_sycee': 5,    # 比武次数 购买
    'plunder_sycee': 5,  # 掠夺次数 购买
    'gethero': 1,        # 免费抽将次数
}

#########################
#      武将             #
#########################
# 武将最高阶数 (初始第1阶)
HERO_MAX_STEP = 5
# 武将升阶消耗多少同名卡魂
HERO_STEP_UP_COST_SOUL_AMOUNT = 2
# 武将升阶花费多少金币
HERO_STEP_UP_COST_GOLD = 1000


#########################
#      装备             #
#########################
# 装备最高等级
EQUIP_MAX_LEVEL = 99
# 装备最高阶数 (初始第0阶)
EQUIP_MAX_STEP= 6
# 装备升阶花费多少金币
EQUIP_STEP_UP_COST_GOLD = 10000


#########################
#      掠夺             #
#########################
# 掠夺超过免费次数后每次掠夺消耗元宝
PLUNDER_COST_SYCEE = 5
# 掠夺失败获得官职经验
PLUNDER_GET_OFFICIAL_EXP_WHEN_LOST = 2
# 掠夺胜利获得官职经验
PLUNDER_GET_OFFICIAL_EXP_WHEN_WIN = 5
# 掠夺胜利获得对方武将概率
PLUNDER_GET_HERO_PROB = 100


#########################
#      战俘             #
#########################
# 战俘初始劝降几率
PRISONER_START_PROB = 10
# 使用一次诏书增加多少劝降几率
PRISONER_INCR_PROB = 10
# 战俘最多可以有多少个
MAX_PRISONERS_AMOUNT = 4
# 增加监狱最大战俘数量花费
PRISON_INCR_AMOUNT_COST = 1
# 增加的监狱战俘数量上限，None为没有上限
PRISON_INCR_MAX_AMOUNT = 6


#########################
#      武将             #
#########################
# 比武超过免费次数后每次比武消耗元宝
ARENA_COST_SYCEE = 5
# 比武胜利获得积分
ARENA_GET_SCORE_WHEN_WIN = 3
# 比武失败获得积分
ARENA_GET_SCORE_WHEN_LOST = 0



#########################
#      武将             #
#########################
# 基本好友最大数量
MAX_FRIENDS_AMOUNT = 5

# 邮件可以保存多少天
MAIL_KEEP_DAYS = 1

# 猛将挑战增加一分钟需要多少元宝
TEAMBATTLE_INCR_COST = 1