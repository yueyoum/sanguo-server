from core.drives import redis_client

EXPIRE = 3600 * 2

keygen = lambda char_id: 'noti:{0}'.format(char_id)

def publish_to_char(char_id, msg):
    key = keygen(char_id)
    redis_client.rpush(key, msg)
    redis_client.expire(key, EXPIRE)


def message_get(char_id):
    key = keygen(char_id)
    msgs = redis_client.lrange(key, 0, -1)
    redis_client.delete(key)
    return msgs


def message_clean(char_id):
    key = keygen(char_id)
    redis_client.delete(key)
