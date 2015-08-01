__author__ = 'wang'

import os
import arrow

from django.conf import settings
from django.core.mail import mail_admins

now = lambda: arrow.utcnow().to(settings.TIME_ZONE).format("YYYY-MM-DD HH:mm:ss")

class Logger(object):
    def __init__(self, name):
        self.name = name
        self.f = open(os.path.join(settings.LOG_PATH, name), 'a')
        print "CRON START: {0}".format(name)

    def write(self, text):
        self.f.write("{0} {1}\n".format(now(), text))

    def error(self, text):
        self.write("==== ERROR ====")
        self.write(text)
        self.write("==== ===== ====")

        html_message = text.replace("\n", "<br/>")
        mail_admins("cron error: {0}".format(self.name), "", fail_silently=True, html_message=html_message)

    def close(self):
        self.f.close()
