from core.drives import redis_client_two


def publish_to_char(char_id, msg):
    redis_client_two.rpush('noti:{0}'.format(char_id), msg)


def message_get(char_id, is_login=False):
    key = 'noti:{0}'.format(char_id)

    if is_login:
        msgs = []
    else:
        msgs = redis_client_two.lrange(key, 0, -1)

    redis_client_two.delete(key)
    return msgs
