import cPickle
from cPickle import HIGHEST_PROTOCOL

from core.drives import redis_client


CACHE_SECONDS = 3600


def set(key, obj, expire=CACHE_SECONDS):
    value = cPickle.dumps(obj, HIGHEST_PROTOCOL)
    redis_client.set(key, value)
    if expire:
        redis_client.expire(key, expire)


def get(key):
    value = redis_client.get(key)
    if value:
        return cPickle.loads(value)
    return None


def delete(key):
    redis_client.delete(key)


