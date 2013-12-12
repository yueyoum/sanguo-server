
from core.signals import hang_finished_signal, prisoner_changed_signal
from core.mongoscheme import Prison

from protomsg import Prisoner as PrisonerProtoMsg

def hang_job(char_id):
    hang_finished_signal.send(
        sender = None,
        char_id = char_id
    )


def prisoner_job(char_id, prisoner_id, status):
    if status == PrisonerProtoMsg.NOT:
        new_status = PrisonerProtoMsg.OUT
    elif status == PrisonerProtoMsg.IN:
        new_status = PrisonerProtoMsg.FINISH
    else:
        raise Exception("prisoner_job, bad status. {0}, {1}, {2}".format(char_id, prisoner_id, status))

    prison = Prison.objects.get(id=char_id)
    prison.prisoners[str(prisoner_id)].status = new_status
    prison.save()
    
    prisoner_changed_signal.send(
        sender = None,
        char_id = char_id,
        mongo_prisoner_obj = prison.prisoners[str(prisoner_id)]
    )
