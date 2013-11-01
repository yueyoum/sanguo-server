import redis
import pymongo

from django.conf import settings

_redis_pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB
        )

redis_client = redis.Redis(connection_pool=_redis_pool)

mongodb_client = pymongo.MongoClient(
        host=settings.MONGODB_HOST,
        port=settings.MONGODB_PORT
        )

mongodb_client_db = mongodb_client[settings.MONGODB_DB]

# mongodb scheme
#
# collection          document
#
# char_formation      {
#                       _id: char_id,
#                       data: proto_binary,
#                     }
#       
# char_stage         {
#                       _id: char_id,
#                       stage_id: True of False,
#                       stage_id: True of False,
#                       ...
#                     }

