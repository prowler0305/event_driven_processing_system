import logging

from order_processor.exceptions import NonRetryableProcessingError, RetryableProcessingError
from order_processor.validation import OrderEventValidator

logger = logging.getLogger(__name__)

class OrderService(object):
    required_fields = ["order_id", "event_id"]
    def __init__(self, order_event):
        self.order_event = order_event
        self.validator = OrderEventValidator(self.order_event)

    @property
    def event_id(self):
        return self.validator.event_id

    @property
    def order_id(self):
        return self.validator.order_id

    @property
    def order_logger(self) -> logging.LoggerAdapter:
        log_ctx = dict(event_id=self.event_id, order_id=self.order_id)
        return logging.LoggerAdapter(logger, log_ctx)

    def process_order(self) -> None:
        """
        Process an order event

        * extract order_id
        * extract event_id
        * extract customer_id
        * process order
            * save to database
            * charge payment
            * reserve inventory
        :return:
        """
        # Validate event contains required fields
        self.validator.validate_order_payload(required_fields=self.required_fields)
        if self.order_event.get("failure_mode") == "non_retryable":
            raise NonRetryableProcessingError("Intentional failure for DLQ test")

        # Will change this block to incorporate the custom exceptions once more logic is implemented
        # to
        self.order_logger.info("Processing order")
        self.save_order()
        self.charge_payment()
        self.reserve_inventory()
        self.order_logger.info("Order processing successful")

        return

    def save_order(self) -> None:
        self.order_logger.info("Saving order...")
        if self.order_event.get("failure_mode") == "retryable":
            raise RetryableProcessingError("Simulated transient failure in save_order()")

    def charge_payment(self) -> None:
        self.order_logger.info("Charge payment...")

    def reserve_inventory(self) -> None:
        self.order_logger.info("Reserve inventory...")
