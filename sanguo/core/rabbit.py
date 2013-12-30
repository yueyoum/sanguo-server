import pika

# FIXME settings
from django.conf import settings

if settings.TESTING:
    vhost = 'sanguo_test'
else:
    vhost = 'sanguo'

MSG_EXCHANGE = 'msg.direct'


class Rabbit(object):
    def __init__(self):
        self._connect()

    def _connect(self):
        param = pika.connection.URLParameters(
            'amqp://guest:guest@127.0.0.1:5672/{0}'.format(vhost)
        )

        connection = pika.BlockingConnection(param)
        self.channel = connection.channel()

        self.channel.exchange_declare(
            exchange=MSG_EXCHANGE,
            exchange_type='direct'
        )


    def bind(self, char_id, server_id):
        queue = 'char.{0}'.format(char_id)

        self.channel.queue_declare(queue=queue)
        self.channel.queue_bind(
            exchange=MSG_EXCHANGE,
            queue=queue,
            routing_key=queue
        )
        self.channel.queue_bind(
            exchange=MSG_EXCHANGE,
            queue=queue,
            routing_key='server.{0}'.format(server_id)
        )


    def publish_to_char(self, char_id, body):
        try:
            self.channel.basic_publish(
                exchange=MSG_EXCHANGE,
                routing_key='char.{0}'.format(char_id),
                body=body
            )
        except Exception as e:
            print "wocao!!!", e
            self._connect()
            self.channel.basic_publish(
                exchange=MSG_EXCHANGE,
                routing_key='char.{0}'.format(char_id),
                body=body
            )


    def publish_to_server(self, server_id, body):
        self.channel.basic_publish(
            exchange=MSG_EXCHANGE,
            routing_key='server.{0}'.format(server_id),
            body=body
        )

    def message_get(self, char_id):
        queue = 'char.{0}'.format(char_id)
        method_frame, header_frame, body = self.channel.basic_get(queue)
        if method_frame:
            self.channel.basic_ack(method_frame.delivery_tag)
            return body

        return None

    def message_get_all(self, char_id):
        msgs = []
        while True:
            m = self.message_get(char_id)
            if not m:
                break
            msgs.append(m)

        return msgs


rabbit = Rabbit()
