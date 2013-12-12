from __future__ import absolute_import
from celery.task.control import revoke

from timer.celery import app

@app.task
def sched(callback, *args):
    callback(*args)


def cancel_job(jobid, terminate=False):
    revoke(jobid, terminate=terminate)


