import pika
import json
import asyncio
from app.config import RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ_QUEUE


def publish_event_sync(data: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE,
        body=json.dumps(data),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()


async def publish_event(data: dict):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, publish_event_sync, data)
