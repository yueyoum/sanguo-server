# -*- coding: utf-8 -*-

__author__ = 'Wang Chao'
__date__ = '5/20/14'

from __future__ import absolute_import
from celery.task.control import revoke

from worker.celery import app

from core.stage import Hang

def cancel(jobid):
    revoke(jobid)

@app.task
def hang_job(char_id, seconds):
    h = Hang(char_id)
    h.finish(actual_seconds=seconds)

