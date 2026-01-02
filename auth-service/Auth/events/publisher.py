import json
import pika
import logging 
logger = logging.getlogger(__name__)

def publish_user_created_event(data):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq")
        )
        channel = connection.channel()

        channel.queue_declare(queue="user_created")

        channel.basic_publish(
            exchange="",
            routing_key="user_created",
            body=json.dumps(data)
        )

        logger.info("EVENT SENT TO RABBITMQ:", data)
        connection.close()

    except Exception as e:
        logger.info("RabbitMQ connection error:", e)
