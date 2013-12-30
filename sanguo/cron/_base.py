__author__ = 'wang'

import os
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanguo.settings')

from django.conf import settings
import core.drives


LOG_PATH = settings.LOG_PATH


class Logger(object):
    def __init__(self, name):
        self.f = open(os.path.join(LOG_PATH, name), 'a')

    def write(self, text):
        now = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S")
        self.f.write("{0} {1}\n".format(now, text))

    def close(self):
        self.f.close()
