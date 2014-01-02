import datetime
import calendar

import pytz

from django.conf import settings

LOCAL_TIMEZONE = pytz.timezone(settings.TIME_ZONE)


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def utc_timestamp():
    d = datetime.datetime.utcnow()
    return calendar.timegm(d.utctimetuple())


def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(LOCAL_TIMEZONE)
    return LOCAL_TIMEZONE.normalize(local_dt)


def localnow():
    return utc_to_local(utcnow())


def local_timestamp():
    return calendar.timegm(localnow().timetuple())


def hours_delta(h):
    now = datetime.datetime.now()
    return now + datetime.timedelta(hours=h)
