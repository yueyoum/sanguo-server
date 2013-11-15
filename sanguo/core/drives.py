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



class _Document(object):
    def __init__(self, db, document):
        self.document = db[document]

    def get(self, key, **extra):
        if extra:
            return self.document.find_one(
                    {'_id': key},
                    extra
                    )

        return self.document.find_one(
                {'_id': key}
                )

    def set(self, key, **kwargs):
        self.document.update(
                {'_id': key},
                {'$set': kwargs},
                upsert=True
                )

    def remove(self, key):
        self.document.remove({'_id': key})

    def add_to_list(self, key, field, value):
        if not isinstance(value, (list, tuple)):
            value = [value]

        self.document.update(
                {'_id': key},
                {'$push': {field: {'$each': value}}},
                )

    def remove_from_list(self, key, field, value):
        if not isinstance(value, (list, tuple)):
            value = [value]

        self.document.update(
                {'_id': key},
                {'$pullAll': {field: value}},
                upsert=True
                )



document_char = _Document(mongodb_client_db, 'char')



# mongodb scheme
#
# collection          document
#
# char               {
#                       _id: char_id,
#                       formation: proto_binary,
#                     }
#       
# char_stage         {
#                       _id: char_id,
#                       stage_id: True of False,
#                       stage_id: True of False,
#                       ...
#                     }

