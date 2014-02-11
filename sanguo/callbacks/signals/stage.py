from core.signals import (
    hang_finished_signal,
    pvp_finished_signal,
    )

from core.notify import (
    arena_notify,
    )

from core.stage import Hang


def hang_finish(char_id, actual_seconds, **kwargs):
    hang = Hang(char_id)
    hang.finish(actual_seconds=actual_seconds)

hang_finished_signal.connect(
    hang_finish,
    dispatch_uid='core.callbacks.stage.hang_finish'
)


def _pvp_finished(char_id, rival_id, win, **kwargs):
    # FIXME
    arena_notify(char_id)


pvp_finished_signal.connect(
    _pvp_finished,
    dispatch_uid='callbacks.signals.stage._pvp_finished'
)
