import cPickle
from cPickle import HIGHEST_PROTOCOL

from django.conf import settings
from core.drives import redis_client
from utils.timezone import hours_delta

CACHE_HOURS = settings.CACHE_HOURS


def set(key, obj, hours=CACHE_HOURS):
    value = cPickle.dumps(obj, HIGHEST_PROTOCOL)
    redis_client.set(key, value)
    if hours:
        redis_client.expireat(key, hours_delta(hours))


def get(key, hours=CACHE_HOURS):
    value = redis_client.get(key)
    if value:
        print "cache hit: ", key
        if hours:
            redis_client.expireat(key, hours_delta(hours))
        return cPickle.loads(value)
    return None


def delete(key):
    redis_client.delete(key)


