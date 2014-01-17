from settings import *

TESTING = True

BROKER_URL = 'amqp://guest:guest@localhost:5672/sanguo_test'

REDIS_DB = 1
MONGODB_DB = 'test_sanguo'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test_sanguo',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}


from django.core.management import call_command
import loaddata
call_command('syncdb')
loaddata.run()

import signal
import sys
from utils.app_test_helper import _redis_teardown_func

def _signal_hander(s, f):
    _redis_teardown_func()
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_hander)

