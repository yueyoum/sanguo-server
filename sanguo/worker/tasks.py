from __future__ import absolute_import
# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '5/20/14'

from celery.task.control import revoke

from worker.celery import app

from core.signals import hang_finished_signal

def cancel(jobid):
    revoke(jobid)

@app.task
def hang_job(char_id, seconds):
    hang_finished_signal.send(
        sender=None,
        char_id=char_id,
        actual_seconds=seconds
    )

