from order_processor.exceptions import NonRetryableProcessingError


class OrderEventValidator(object):
    def __init__(self, order_event: dict):
        if not isinstance(order_event, dict):
            raise NonRetryableProcessingError("Event payload must be a dictionary")
        self.order_event = order_event

    @property
    def event_id(self):
        if not self.order_event.get("event_id"):
            raise NonRetryableProcessingError("Missing required field: event_id")
        return self.order_event["event_id"]
    @property
    def order_id(self):
        if not self.order_event.get("order_id"):
            raise NonRetryableProcessingError("Missing required field: order_id")
        return self.order_event["order_id"]

    def validate_envelope(self) -> None:
        if not self.order_event.get("event_id"):
            raise NonRetryableProcessingError("Missing required field: event_id")

    def validate_order_payload(self, required_fields: list[str]) -> None:
        """
        For a given list of fields validate that they exist in the order_event. For each one
        found that doesn't exist add it a list that is returned.

        *Note that this only looks at the order_events highest level keys/fields and does not search in
        nested objects.
        :param required_fields:
        :return:
        """
        missing = [field for field in required_fields if not self.order_event.get(field)]
        if missing:
            raise NonRetryableProcessingError(f"Missing required fields: {missing}")
