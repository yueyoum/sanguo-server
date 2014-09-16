# -*- coding: utf-8 -*-

from core.signals import (
    pve_finished_signal,
    )

from core.achievement import Achievement
from core.task import Task

from core.affairs import Affairs, FIRST_CITY_ID

from preset.data import STAGES

def pve_finish(char_id, stage_id, win, star, **kwargs):
    achievement = Achievement(char_id)
    if win:
        achievement.trig(7, stage_id)
        if star:
            achievement.trig(9, 1)

        t = Task(char_id)
        t.trig(1)
    else:
        achievement.trig(8, 1)


    # 城镇
    # 自动开启第一个城镇，并且自动开始挂机
    if win:
        if STAGES[stage_id].battle_end:
            affairs = Affairs(char_id)
            new_opened = affairs.open_city(STAGES[stage_id].battle)
            if STAGES[stage_id].battle == FIRST_CITY_ID and new_opened:
                affairs.start_hang(FIRST_CITY_ID)


pve_finished_signal.connect(
    pve_finish,
    dispatch_uid='core.callbacks.stage.pve_finish'
)

