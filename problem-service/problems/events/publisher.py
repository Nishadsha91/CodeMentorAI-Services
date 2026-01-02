import pika
import json

def publish_event(queue_name, data):
    try:
        print("SENDING EVENT TO RABBITMQ:", queue_name, data)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq")
        )
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(data)
        )
        print(f"Event sent → {queue_name}: {data}")
        connection.close()
    except Exception as e:
        print("Error publishing event:", e)
