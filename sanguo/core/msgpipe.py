from core.drives import redis_client


def publish_to_char(char_id, msg):
    redis_client.rpush('noti:{0}'.format(char_id), msg)


def message_get(char_id):
    from core.msgpublish import ChatMessagePublish
    ChatMessagePublish(char_id).send_notify()

    key = 'noti:{0}'.format(char_id)
    msgs = redis_client.lrange(key, 0, -1)
    redis_client.delete(key)

    return msgs

def message_clean(char_id):
    key = 'noti:{0}'.format(char_id)
    redis_client.delete(key)
