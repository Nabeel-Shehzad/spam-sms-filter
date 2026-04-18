"""
Kafka consumer — reads from 'sms-incoming', classifies each message,
and publishes the result to 'sms-classified'.

Run as a standalone process:
    python -m backend.streaming.consumer
"""

import json
import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_INCOMING = "sms-incoming"
TOPIC_CLASSIFIED = "sms-classified"


def run_consumer():
    from kafka import KafkaConsumer, KafkaProducer
    from backend.ml.predictor import classify

    consumer = KafkaConsumer(
        TOPIC_INCOMING,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="spam-filter-group",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"[Consumer] Listening on topic '{TOPIC_INCOMING}' ...")

    for message in consumer:
        payload = message.value
        text = payload.get("text", "")
        if not text:
            continue

        result = classify(text)
        result["original_text"] = text
        result["source_metadata"] = {k: v for k, v in payload.items() if k != "text"}

        producer.send(TOPIC_CLASSIFIED, value=result)
        print(f"[Consumer] '{text[:60]}...' -> {result['label']} ({result['confidence']:.2f})")


if __name__ == "__main__":
    run_consumer()
