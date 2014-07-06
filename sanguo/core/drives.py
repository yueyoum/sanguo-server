import redis
import pymongo
from mongoengine import connect

from django.conf import settings


redis_client = None
redis_client_two = None
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
    global redis_client
    global redis_client_two
    global mongodb_client
    global mongodb_client_db
    global document_ids

    if redis_client is not None:
        return

    _redis_pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB
    )

    redis_client = redis.Redis(connection_pool=_redis_pool)

    _redis_pool_two = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB+2
    )

    redis_client_two = redis.Redis(connection_pool=_redis_pool_two)

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
