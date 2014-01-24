from core.signals import (
    hang_finished_signal,
    hang_add_signal,
    hang_cancel_signal,
    pvp_finished_signal,

    )

from core.notify import (
    hang_notify,
    prize_notify,

    arena_notify,
    )


def hang_add(char_id, hours, **kwargs):
    hang_notify(char_id)


def hang_finish(char_id, actual_hours=None, **kwargs):
    from core.mongoscheme import Hang

    print "hang_finish", char_id
    hang = Hang.objects.get(id=char_id)
    if not actual_hours:
        actual_hours = hang.hours

    hang.actual_hours = actual_hours
    hang.finished = True
    hang.save()
    hang_notify(char_id, hang=hang)
    prize_notify(char_id, 1)


def hang_cancel(char_id, actual_hours, **kwargs):
    print "hang_cancel", char_id
    hang_finish(char_id, actual_hours=actual_hours)


hang_add_signal.connect(
    hang_add,
    dispatch_uid='core.callbacks.stage.hang_add'
)

hang_finished_signal.connect(
    hang_finish,
    dispatch_uid='core.callbacks.stage.hang_finish'
)

hang_cancel_signal.connect(
    hang_cancel,
    dispatch_uid='core.callbacks.stage.hang_cancel'
)


def _pvp_finished(char_id, rival_id, win, **kwargs):
    # FIXME
    arena_notify(char_id)


pvp_finished_signal.connect(
    _pvp_finished,
    dispatch_uid='callbacks.signals.stage._pvp_finished'
)
