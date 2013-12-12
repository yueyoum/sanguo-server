from __future__ import absolute_import
from celery.task.control import revoke

from timer.celery import app

from django.conf import settings
TESTING = settings.TESTING

class MockObject(object):
    def __init__(self):
        self.id = 'mock'
    
    def apply_async(self, *args, **kwargs):
        return self
    
    def __call__(self, *args, **kwargs):
        pass

mockobject = MockObject()

def _mock(func):
    if TESTING:
        return mockobject
    
    def deco(*args, **kwargs):
        return func(*args, **kwargs)
    return deco

    

@_mock
@app.task
def sched(callback, *args):
    callback(*args)


@_mock
def cancel_job(jobid, terminate=False):
    revoke(jobid, terminate=terminate)


