import pika

# FIXME settings
from django.conf import settings

if settings.TESTING:
    vhost = 'sanguo_test'
else:
    vhost = 'sanguo'

param = pika.connection.URLParameters(
        'amqp://guest:guest@127.0.0.1:5672/{0}'.format(vhost)
        )

connection = pika.BlockingConnection(param)
channel = connection.channel()


MSG_EXCHANGE = 'msg.direct'


channel.exchange_declare(
        exchange = MSG_EXCHANGE,
        exchange_type = 'direct'
        )



def bind(char_id, server_id):
    queue = 'char.{0}'.format(char_id)

    channel.queue_declare(queue=queue)
    channel.queue_bind(
            exchange = MSG_EXCHANGE,
            queue = queue,
            routing_key = queue
            )
    channel.queue_bind(
            exchange = MSG_EXCHANGE,
            queue = queue,
            routing_key = 'server.{0}'.format(server_id)
            )


def publish_to_char(char_id, body):
    channel.basic_publish(
            exchange = MSG_EXCHANGE,
            routing_key = 'char.{0}'.format(char_id),
            body = body
            )

def publish_to_server(server_id, body):
    channel.basic_publish(
            exchange = MSG_EXCHANGE,
            routing_key = 'server.{0}'.format(server_id),
            body = body
            )

def message_get(char_id):
    queue = 'char.{0}'.format(char_id)
    method_frame, header_frame, body = channel.basic_get(queue)
    if method_frame:
        channel.basic_ack(method_frame.delivery_tag)
        return body

    return None

def message_get_all(char_id):
    msgs = []
    while True:
        m = message_get(char_id)
        if not m:
            break
        msgs.append(m)

    return msgs

