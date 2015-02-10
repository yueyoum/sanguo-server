# -*- coding: utf-8 -*-

from core.signals import (
    pve_finished_signal,
    )

from core.achievement import Achievement
from core.task import Task

from core.affairs import Affairs
from core.activity import ActivityStatic

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


    # 开启城镇
    if win:
        if STAGES[stage_id].battle_open:
            affairs = Affairs(char_id)
            affairs.open_city(STAGES[stage_id].battle)

    # 判断活动
    if win:
        ActivityStatic(char_id).trig(3001)


pve_finished_signal.connect(
    pve_finish,
    dispatch_uid='core.callbacks.stage.pve_finish'
)

