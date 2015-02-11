# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '15-2-4'


# 运行一次，用于给玩家武将加上五行属性

import os
import sys

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_PATH = os.path.normpath(os.path.join(CURRENT_PATH, '../sanguo'))

os.chdir(PROJECT_PATH)
sys.path.append(PROJECT_PATH)

os.environ['DJANGO_SETTINGS_MODULE'] = 'sanguo.settings'

from core.mongoscheme import MongoHero, MongoEmbeddedHeroWuxing
from preset.data import HEROS


def init1():
    # 首次初始化

    for h in MongoHero.objects.all():
        wx = HEROS[h.oid].wuxings[0]
        if str(wx) in h.wuxings:
            continue

        h.wuxings[str(wx)] = MongoEmbeddedHeroWuxing(level=1, exp=0)
        h.save()

if __name__ == '__main__':
    init1()
