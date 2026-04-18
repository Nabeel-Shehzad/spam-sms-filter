"""
Kafka producer — publishes incoming SMS messages to the 'sms-incoming' topic.

Usage:
    from backend.streaming.producer import publish_sms
    publish_sms("Win a free prize now!")
"""

import json
import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_INCOMING = "sms-incoming"

_producer = None


def _get_producer():
    global _producer
    if _producer is None:
        try:
            from kafka import KafkaProducer
            _producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except Exception as e:
            print(f"[Kafka producer] Could not connect: {e}. Streaming disabled.")
    return _producer


def publish_sms(text: str, metadata: dict | None = None) -> bool:
    """Publish an SMS to the incoming topic. Returns True on success."""
    producer = _get_producer()
    if producer is None:
        return False
    try:
        payload = {"text": text, **(metadata or {})}
        producer.send(TOPIC_INCOMING, value=payload)
        producer.flush()
        return True
    except Exception as e:
        print(f"[Kafka producer] Send failed: {e}")
        return False
