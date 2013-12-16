from core.signals import (
    prisoner_add_signal,
    prisoner_changed_signal,
    prisoner_del_signal,
)

from core.notify import (
    new_prisoner_notify,
    update_prisoner_notify,
    remove_prisoner_notify,
)

def prisoner_add(char_id, mongo_prisoner_obj, **kwargs):
    new_prisoner_notify(char_id, mongo_prisoner_obj)

def prisoner_change(char_id, mongo_prisoner_obj, **kwargs):
    print "prisoner_change,", char_id, mongo_prisoner_obj
    update_prisoner_notify(char_id, mongo_prisoner_obj)


def prisoner_del(char_id, prisoner_id, **kwargs):
    print 'prisoner_del,', char_id, prisoner_id
    remove_prisoner_notify(char_id, prisoner_id)



prisoner_add_signal.connect(
    prisoner_add,
    dispatch_uid = 'core.callbacks.stage.prisoner_add'
)


prisoner_changed_signal.connect(
    prisoner_change,
    dispatch_uid = 'callbacks.prison.prisoner_change'
)

prisoner_del_signal.connect(
    prisoner_del,
    dispatch_uid = 'callbacks.prison.prisoner_del'
)
