from core.signals import hang_finished_signal, hang_add_signal, hang_cancel_signal

from core import notify
from core.mongoscheme import Hang, MongoChar
from utils import timezone

from cronjob.scheduler import add_hang_job, cancel_hang_job


def hang_add(char_id, stage_id, hours, **kwargs):
    print "hang_add", char_id, stage_id, hours
    hang = Hang(
        id = char_id,
        stage_id = stage_id,
        hours = hours,
        start = timezone.utc_timestamp(),
        finished = False
    )
    
    hang.save()
    
    mongo_char = MongoChar.objects.only('hang_hours').get(id=char_id)
    # FIXME
    hang_hours = mongo_char.hang_hours or 8
    mongo_char.hang_hours = hang_hours - hours
    mongo_char.save()
    
    add_hang_job(char_id, hours)

    notify.hang_notify_with_data(
        'noti:{0}'.format(char_id),
        mongo_char.hang_hours,
        hang
        )


def hang_finish(char_id, **kwargs):
    print "hang_finish", char_id
    Hang.objects(id=char_id).update_one(set__finished=True)
    notify.hang_notify('noti:{0}'.format(char_id), char_id)
    notify.prize_notify('noti:{0}'.format(char_id), 1)



def hang_cancel(char_id, **kwargs):
    print "hang_cancel", char_id
    hang = Hang.objects.get(id=char_id)
    mongo_char = MongoChar.objects.only('hang_hours').get(id=char_id)
    utc_now_timestamp = timezone.utc_timestamp()
    
    original_h = hang.hours
    h, s = divmod((utc_now_timestamp - hang.start), 3600)
    if s:
        h += 1
    print 'original_h =', original_h, 'h =', h
    
    mongo_char.hang_hours += original_h - h
    mongo_char.save()
    
    cancel_hang_job(char_id)
    hang_finish(char_id)


hang_add_signal.connect(
    hang_add,
    dispatch_uid = 'core.callbacks.stage.hang_add'
)

hang_finished_signal.connect(
    hang_finish,
    dispatch_uid = 'core.callbacks.stage.hang_finish'
)

hang_cancel_signal.connect(
    hang_cancel,
    dispatch_uid = 'core.callbacks.stage.hang_cancel'
)
