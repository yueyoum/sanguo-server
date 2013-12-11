from core.signals import (
    hang_finished_signal,
    hang_add_signal,
    hang_cancel_signal,
    pve_finished_signal,
    
    prisoner_add_signal,
    )


from core.notify import (
    #hang_notify_with_data,
    hang_notify,
    prize_notify,
    
    current_stage_notify,
    new_stage_notify,
    
    new_prisoner_notify,
)

from cronjob.scheduler import add_hang_job, cancel_hang_job


def hang_add(char_id, hours, **kwargs):
    add_hang_job(char_id, hours)
    hang_notify('noti:{0}'.format(char_id), char_id)


def hang_finish(char_id, **kwargs):
    from core.mongoscheme import Hang
    print "hang_finish", char_id
    Hang.objects(id=char_id).update_one(set__finished=True)
    hang_notify('noti:{0}'.format(char_id), char_id)
    prize_notify('noti:{0}'.format(char_id), 1)



def hang_cancel(char_id, **kwargs):
    print "hang_cancel", char_id
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




def _pve_finished(char_id, stage_id, win, star, **kwargs):
    from core.mongoscheme import MongoChar
    print "_pve_finished", char_id, stage_id, win, star
    current_stage_notify('noti:{0}'.format(char_id), stage_id, star)
    
    char = MongoChar.objects.only('stages', 'stage_new').get(id=char_id)
    stages = char.stages
    if win:
        # FIXME
        char.stages[str(stage_id)] = star
        new_stage_id = stage_id + 1
        if char.stage_new != new_stage_id:
            char.stage_new = new_stage_id
            
            if str(new_stage_id) not in stages.keys():
                new_stage_notify('noti:{0}'.format(char_id), new_stage_id)
        
        char.save()
        


pve_finished_signal.connect(
    _pve_finished,
    dispatch_uid = 'core.stage._pve_finished'
)


def prisoner_add(char_id, mongo_prisoner_obj, **kwargs):
    new_prisoner_notify('noti:{0}'.format(char_id), mongo_prisoner_obj)

prisoner_add_signal.connect(
    prisoner_add,
    dispatch_uid = 'core.callbacks.stage.prisoner_add'
)

