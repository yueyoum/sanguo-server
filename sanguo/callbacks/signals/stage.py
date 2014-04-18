from core.signals import (
    hang_finished_signal,
    pve_finished_signal,
    )

from core.stage import Hang
from core.achievement import Achievement
from core.task import Task

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


def hang_finish(char_id, actual_seconds, **kwargs):
    hang = Hang(char_id)
    hang.finish(actual_seconds=actual_seconds)

hang_finished_signal.connect(
    hang_finish,
    dispatch_uid='core.callbacks.stage.hang_finish'
)

pve_finished_signal.connect(
    pve_finish,
    dispatch_uid='core.callbacks.stage.pve_finish'
)

