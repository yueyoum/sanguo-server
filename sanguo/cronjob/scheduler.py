import datetime
from apscheduler.scheduler import Scheduler

from core.signals import hang_finished_signal

sched = Scheduler()
sched.start()


def hang_job(char_id):
    hang_finished_signal.send(
        sender = None,
        char_id = char_id
    )



HANG_JOB = {}

def add_hang_job(char_id, hours):
    now = datetime.datetime.now()
    job_at = now + datetime.timedelta(hours=hours)
    
    job = sched.add_date_job(hang_job, job_at, [char_id])
    HANG_JOB[char_id] = job
    print "add_hang_job:", job

def cancel_hang_job(char_id):
    try:
        job = HANG_JOB[char_id]
        sched.unschedule_job(job)
        print "cancel_hang_job:", job
    except KeyError:
        pass

    
