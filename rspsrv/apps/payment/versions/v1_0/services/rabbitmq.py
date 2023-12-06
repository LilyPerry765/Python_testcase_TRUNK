import json
import os
import pika
from celery import shared_task


@shared_task
def rabbitmq_publish_async(message):
    RabbitMQ.publish(message)


class RabbitMQ:
    host = os.environ.get('RSPSRV_RABBITMQ_HOST')
    port = os.environ.get('RSPSRV_RABBITMQ_PORT')
    queue = os.environ.get('RSPSRV_RABBITMQ_QUEUE')
    username = os.environ.get('RSPSRV_RABBITMQ_USER')
    password = os.environ.get('RSPSRV_RABBITMQ_PASSWORD')
    timeout = os.environ.get('RSPSRV_RABBITMQ_TIMEOUT')

    @classmethod
    def publish(cls, msg):

        credentials = pika.PlainCredentials(cls.username, cls.password)
        parameters = pika.ConnectionParameters(
            cls.host,
            int(cls.port),
            '/',
            credentials,
            blocked_connection_timeout=float(cls.timeout)
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=cls.queue, durable=True, arguments={
            'x-queue-mode': "lazy",
        })

        message = json.dumps(msg).encode('utf-8')
        channel.basic_publish(exchange='', routing_key=cls.queue, body=message)
        connection.close()
        print('Message sent to queue {0:s}'.format(cls.queue))

