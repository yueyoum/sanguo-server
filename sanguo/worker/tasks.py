from __future__ import absolute_import
from celery.task.control import revoke


from core.signals import hang_finished_signal, prisoner_changed_signal
from core.mongoscheme import MongoPrison

from protomsg import Prisoner as PrisonerProtoMsg


from worker.celery import app


def cancel(jobid, terminate=False):
    revoke(jobid, terminate=terminate)

@app.task
def hang_finish(char_id):
    hang_finished_signal.send(
        sender=None,
        char_id=char_id
    )

@app.task
def prisoner_change(char_id, prisoner_id, status):
    if status == PrisonerProtoMsg.NOT:
        new_status = PrisonerProtoMsg.OUT
    elif status == PrisonerProtoMsg.IN:
        new_status = PrisonerProtoMsg.FINISH
    else:
        raise Exception("prisoner_job, bad status. {0}, {1}, {2}".format(char_id, prisoner_id, status))

    prison = MongoPrison.objects.get(id=char_id)
    prison.prisoners[str(prisoner_id)].status = new_status
    prison.save()

    prisoner_changed_signal.send(
        sender=None,
        char_id=char_id,
        mongo_prisoner_obj=prison.prisoners[str(prisoner_id)]
    )

