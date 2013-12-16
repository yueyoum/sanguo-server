import cPickle
from cPickle import HIGHEST_PROTOCOL

from django.conf import settings
from core.drives import redis_client
from utils.timezone import hours_delta

CACHE_HOURS = settings.CACHE_HOURS

def set(key, obj, hours=CACHE_HOURS):
    value = cPickle.dumps(obj, HIGHEST_PROTOCOL)
    redis_client.set(key, value)
    redis_client.expireat(key, hours_delta(hours))
    
def get(key):
    value = redis_client.get(key)
    print "cache hit: ", key
    if value:
        redis_client.expireat(key, hours_delta(CACHE_HOURS))
        return cPickle.loads(value)
    return None


def delete(key):
    redis_client.delete(key)


