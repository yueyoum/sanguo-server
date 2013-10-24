import redis

from django.conf import settings


class RedisClientWrapper(object):
    def __init__(self):
        _db_no = settings.REDIS_TEST_DB if settings.TESTING else settings.REDIS_DB

        _redis_pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=_db_no
                )

        self.redis_client = redis.Redis(connection_pool=_redis_pool)

    def __getattr__(self, name):
        return getattr(self.redis_client, name)

redis_client = RedisClientWrapper()

