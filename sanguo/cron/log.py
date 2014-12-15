__author__ = 'wang'

import os
import arrow

from django.conf import settings

class Logger(object):
    def __init__(self, name):
        self.f = open(os.path.join(settings.LOG_PATH, name), 'a')

    def write(self, text):
        now = arrow.utcnow().to(settings.TIME_ZONE).format('YYYY-MM-DD HH:mm:ss')
        self.f.write("{0} {1}\n".format(now, text))

    def close(self):
        self.f.close()
