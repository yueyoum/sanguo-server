from core.drives import redis_client_two


def publish_to_char(char_id, msg):
    redis_client_two.rpush('noti:{0}'.format(char_id), msg)


def message_get(char_id):
    key = 'noti:{0}'.format(char_id)
    msgs = redis_client_two.lrange(key, 0, -1)
    redis_client_two.delete(key)
    return msgs

def message_clean(char_id):
    key = 'noti:{0}'.format(char_id)
    redis_client_two.delete(key)
