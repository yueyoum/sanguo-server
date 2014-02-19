from core.signals import (
    hang_finished_signal,
    )

from core.stage import Hang


def hang_finish(char_id, actual_seconds, **kwargs):
    hang = Hang(char_id)
    hang.finish(actual_seconds=actual_seconds)

hang_finished_signal.connect(
    hang_finish,
    dispatch_uid='core.callbacks.stage.hang_finish'
)

