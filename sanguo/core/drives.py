import redis
import pymongo
from mongoengine import connect

from django.conf import settings

_initialized = False
redis_client = None
redis_client_persistence = None
mongodb_client = None
mongodb_client_db = None
document_ids = None


class _DocumentIds(object):
    def __init__(self, db):
        self.document = db['ids']

    def inc(self, name, value=1):
        res = self.document.find_and_modify(
            query={'_id': name},
            update={'$inc': {'id': value}},
            fields={'_id': 0},
            upsert=True,
            new=True
        )
        return res['id']


def _init():
    global _initialized
    global redis_client
    global redis_client_persistence
    global mongodb_client
    global mongodb_client_db
    global document_ids

    if _initialized:
        return

    _initialized = True

    _redis_pool = redis.ConnectionPool(
        host=settings.REDIS_CACHE_HOST,
        port=settings.REDIS_CACHE_PORT,
        db=0
    )

    redis_client = redis.Redis(connection_pool=_redis_pool)

    _redis_pool_persistence = redis.ConnectionPool(
        host=settings.REDIS_PERSISTENCE_HOST,
        port=settings.REDIS_PERSISTENCE_PORT,
        db=0
    )

    redis_client_persistence = redis.Redis(connection_pool=_redis_pool_persistence)

    mongodb_client = pymongo.MongoClient(
        host=settings.MONGODB_HOST,
        port=settings.MONGODB_PORT
    )

    mongodb_client_db = mongodb_client[settings.MONGODB_DB]

    connect(settings.MONGODB_DB,
            host=settings.MONGODB_HOST,
            port=settings.MONGODB_PORT
    )

    document_ids = _DocumentIds(mongodb_client_db)


_init()
