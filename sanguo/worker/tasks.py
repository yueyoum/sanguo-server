from __future__ import absolute_import
# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '5/20/14'


from worker.celery import app

def cancel(jobid):
    app.control.revoke(jobid, terminate=True)

@app.task
def hang_job(char_id, seconds):
    from core.stage import Hang
    hang = Hang(char_id)
    hang.finish(actual_seconds=seconds)
