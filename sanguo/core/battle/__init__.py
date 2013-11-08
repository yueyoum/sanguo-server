import os
import logging
from logging import handlers

from django.conf import settings

log = logging.getLogger('battle')
log.setLevel(logging.DEBUG)

fmt = logging.Formatter("%(levelname)s: %(message)s")

file_handle = handlers.TimedRotatingFileHandler(
        os.path.join(settings.TMP_PATH, 'battle.log'),
        when='D',
        backupCount=30
        )

file_handle.setLevel(logging.DEBUG)
file_handle.setFormatter(fmt)

log.addHandler(file_handle)

if settings.DEBUG:
    stream_handle = logging.StreamHandler()
    stream_handle.setFormatter(fmt)
    log.addHandler(stream_handle)

