from core.signals import (
    hang_finished_signal,
    pve_finished_signal,
    )

from core.stage import Hang
from core.functionopen import FunctionOpen


def pve_finish(char_id, stage_id, win, star, **kwargs):
    if win:
        fo = FunctionOpen(char_id)
        fo.trig_by_stage_id(stage_id)


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

