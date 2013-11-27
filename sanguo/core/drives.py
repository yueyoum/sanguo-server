import redis
import pymongo
from mongoengine import connect

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

connect(settings.MONGODB_DB,
        host = settings.MONGODB_HOST,
        port = settings.MONGODB_PORT
        )


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
    
    def unset(self, key, fields):
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        
        data = {k: 1 for k in fields}
        self.document.update(
            {'_id': key},
            {'$unset': data}
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

document_ids = _DocumentIds(mongodb_client_db)
#document_char = _Document(mongodb_client_db, 'char')
#document_hero = _Document(mongodb_client_db, 'hero')
#document_stage = _Document(mongodb_client_db, 'stage')
#document_equip = _Document(mongodb_client_db, 'equip')


# mongodb scheme
#
# collection          document
#
# ids                {
#                       _id: type_name,
#                       id: integer,
#                    }
#
# char               {
#                       _id: char_id,
#                       socket: {
#                           1: {
#                                   hero:,
#                                   waepon:,
#                                   armor:,
#                                   jewelry:,
#                               }
#                       }
#                       formation: [socket_id, ...],
#                     }
#
# hero              {
#                       _id: hero_id,
#                       char: char_id
#                   }
#
# stage              {
#                       _id: char_id,
#                       stage_id: True of False,
#                       stage_id: True of False,
#                       ...
#                       new:
#                    }

# equip              {
#                       _id: id from ids `equip`,
#                       oid: integer,
#                       level: integer,
#                       exp: integer,
#                       extra: {attrid: {value:, is_percent:}}
#                    }

