import json

from flask import g, current_app
from kafka import KafkaProducer


def get_kafka_producer():
    """
    Lazily create a Kafka producer and store it in Flask's request context to cache it
    :return:
    """
    if "kafka_producer" not in g:
        g.kafka_producer = KafkaProducer(bootstrap_servers=current_app.config.get("KAFKA_BROKER"),
                      value_serializer=lambda v: json.dumps(v).encode("utf-8")
                      )

    return g.kafka_producer

def close_kafka_producer(exception=None):
    """
    Close the producer at request if it exists
    :param exception:
    :return:
    """
    producer = g.pop("kafka_producer", None)

    if producer is not None:
        producer.close()
