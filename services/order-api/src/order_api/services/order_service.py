import uuid
from datetime import datetime

from flask import current_app

from order_api.kafka_helpers.producer import get_kafka_producer
from shared.schema_loader import load_schema

def generate_id():
    return str(uuid.uuid4())

def create_order_event(data):
    """
    Handles creating the order event and sending to Kafka

    :param data:
    :return:
    """
    producer = None
    if current_app.config.get("KAFKA_ENABLED"):
        producer = get_kafka_producer()

    event = load_schema("order_event.json")

    # set order event id and order id
    event["event_id"] = data.get("event_id") or generate_id()
    event["order_id"] = generate_id()
    # Update order_event schema template with current order request data. Request data and event json keys must match.
    for event_key in event:
        if event_key not in ["event_id", "order_id", "event_type"]:
            event[event_key] = data.get(event_key)
    # Set timestamp for order event
    event["created_at"] = datetime.utcnow().isoformat() + "Z"

    # Send event to Kafka if flag enabled.
    if producer is not None:
        producer.send(current_app.config.get("KAFKA_TOPIC"), value=event)
        producer.flush()
    else:
        current_app.logger.info(f"KAFKA integration not enabled. Set KAFKA_ENABLED to True. Event would have sent: {event}")

    return {"event_id": event.get("event_id"), "order_id": event.get("order_id")}