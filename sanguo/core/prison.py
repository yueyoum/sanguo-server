from core.mongoscheme import Prison, Prisoner
from timer.tasks import sched
from callbacks import timers
from protomsg import Prisoner as PrisonerProtoMsg

from utils import timezone

from core.signals import prisoner_add_signal

def save_prisoner(char_id, oid):
    prison = Prison.objects.only('prisoners').get(id=char_id)
    prisoner_ids = [int(i) for i in prison.prisoners.keys()]
    
    new_persioner_id = 1
    while True:
        if new_persioner_id not in prisoner_ids:
            break
        new_persioner_id += 1
    
    # FIXME
    job = sched.apply_async(
        [timers.prisoner_job, char_id, new_persioner_id, PrisonerProtoMsg.NOT],
        countdown = 10
    )
    
    
    p = Prisoner()
    p.id = new_persioner_id
    p.oid = oid
    p.start_time = timezone.utc_timestamp()
    p.status = PrisonerProtoMsg.NOT
    p.jobid = job.id
    
    
    prison.prisoners[str(new_persioner_id)] = p
    prison.save()
    
    prisoner_add_signal.send(
        sender = None,
        char_id = char_id,
        mongo_prisoner_obj = p
    )
    
    return p