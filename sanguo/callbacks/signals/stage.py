from core.signals import (
    hang_finished_signal,
    hang_add_signal,
    hang_cancel_signal,
    pve_finished_signal,
    pvp_finished_signal,
    
    )


from core.notify import (
    hang_notify,
    prize_notify,
    
    current_stage_notify,
    new_stage_notify,
    
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
    hang_notify(char_id, hang=hang)
    if actual_hours:
        prize_notify(char_id, 1)



def hang_cancel(char_id, actual_hours, **kwargs):
    print "hang_cancel", char_id
    hang_finish(char_id, actual_hours=actual_hours)


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
    if win:
        current_stage_notify(char_id, stage_id, star)
    
    char = MongoChar.objects.only('stages', 'stage_new').get(id=char_id)
    stages = char.stages
    if win:
        # FIXME
        char.stages[str(stage_id)] = star
        char.stage_new = 0
        new_stage_id = stage_id + 1
        if char.stage_new != new_stage_id:
            char.stage_new = new_stage_id
            
            if str(new_stage_id) not in stages.keys():
                new_stage_notify(char_id, new_stage_id)
        
        char.save()
        


pve_finished_signal.connect(
    _pve_finished,
    dispatch_uid = 'core.stage._pve_finished'
)



def _pvp_finished(char_id, rival_id, win, **kwargs):
    # FIXME
    arena_notify(char_id)


pvp_finished_signal.connect(
    _pvp_finished,
    dispatch_uid = 'callbacks.signals.stage._pvp_finished'
)
