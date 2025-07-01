import os
import json
import pika
import asyncio
import uuid
from datetime import datetime

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME")
AGENT_ID = os.getenv("AGENT_ID")

_credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
_params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=_credentials)

def _create_connection():
    return pika.BlockingConnection(_params)

async def send_message(sender, message, receiver="", conversation_id=None, in_response_to=None):
    payload = {
        "message_id": str(uuid.uuid4()),
        "conversation_id": conversation_id or str(uuid.uuid4()),
        "sender": sender,
        "receiver": receiver,
        "message": message,
        "in_response_to": in_response_to,
        "timestamp": datetime.utcnow().isoformat()
    }
    connection = _create_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key='',
        body=json.dumps(payload)
    )
    connection.close()
    print(f"[📤 {sender}] Mensaje enviado: {payload}")

def subscribe_messages(callback):
    connection = _create_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

    def _on_message(ch, method, props, body):
        try:
            payload = json.loads(body)
            asyncio.run(callback(payload))
        except Exception as e:
            print("[⚠️ Error procesando mensaje]", e)

    channel.basic_consume(queue=queue_name, on_message_callback=_on_message, auto_ack=True)
    channel.start_consuming()
