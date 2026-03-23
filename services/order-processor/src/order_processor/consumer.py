import json
import logging
from datetime import datetime
from time import sleep

from order_processor.config.config import config
from order_processor.exceptions import DuplicateEventError, RetryableProcessingError, NonRetryableProcessingError
from order_processor.service.order_service import OrderService
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaTimeoutError, KafkaConnectionError, NoBrokersAvailable, NodeNotReadyError, \
    KafkaConfigurationError

from order_processor.validation import OrderEventValidator

logger = logging.getLogger(__name__)

class Consumer(object):
    def __init__(self):
        self.dlq_producer = None
        self.bootstrap_servers = config.kafka_bootstrap_servers
        self.group_id = config.consumer_group
        self.consumer = None
        self.processed_events = set()
        self.dlq_topic = config.dlq_topic
        self.topic = config.orders_topic
        self.offset_reset = config.auto_offset_reset
        self.log_ctx = None
        self.consumer_logger = logger
        self.max_retries = config.max_retries

    def create_consumer(self):
        if self.consumer is None:
            try:
                self.consumer = KafkaConsumer(self.topic,
                                              bootstrap_servers=self.bootstrap_servers,
                                              group_id=self.group_id,
                                              enable_auto_commit=False,
                                              auto_offset_reset=self.offset_reset,
                                              value_deserializer=lambda v: json.loads(v.decode("utf-8")))
                logger.info("Consumer created successfully")
            except KafkaConfigurationError:
                logger.exception(f"KafkaConsumer object can't be created due to configuration error")

    def create_dlq_producer(self):
        """
        Lazily create the dlq producer if it doesn't exist.
        :return:
        """
        if self.dlq_producer is None:
            self.dlq_producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers,
                                              value_serializer=lambda v: json.dumps(v).encode("utf-8")
                                             )

    def start(self):
        """
        Starts the consumer loop with the consumer object.
        :return:
        """
        # Lazily create the KafkaConsumer if it isn't already initialized.
        if self.consumer is None:
            self.create_consumer()

        if isinstance(self.consumer, KafkaConsumer):
            logger.info("Starting consumer...")
            while True:
                try:
                    records = self.consumer.poll(timeout_ms=1000)
                    for topic_partition, messages in records.items():
                        for record in messages:
                            order_event = record.value
                            try:
                                validator = OrderEventValidator(order_event)
                                event_id = validator.event_id
                                self.log_ctx = dict(event_id=event_id)
                                self.consumer_logger = logging.LoggerAdapter(logger, self.log_ctx)
                                if event_id in self.processed_events:
                                    raise DuplicateEventError()
                                self.process_event_with_retries(order_event)
                                self.processed_events.add(event_id)
                                self.consumer.commit()
                            except DuplicateEventError as exc:
                                self.consumer_logger.info(f"Duplicate event detected: {event_id} - skipping")
                                self.consumer.commit() # Commit this duplicate offset so we don't process forever.
                                continue
                            except RetryableProcessingError as exc:
                                self.send_to_dlq(record, exc, failure_category="retryable_exhausted", retry_count=self.max_retries)
                                self.consumer.commit()
                            except NonRetryableProcessingError as exc:
                                self.consumer_logger.error("Non-retryable processing failure")
                                self.send_to_dlq(record, exc, failure_category="non_retryable")
                                self.consumer.commit()
                            except Exception as exc:
                                self.consumer_logger.exception("Unexpected processing failure")
                                # send this to DLQ topic.
                                self.send_to_dlq(record, exc, failure_category="unexpected")
                                self.consumer.commit()

                except (KafkaTimeoutError, KafkaConnectionError, NoBrokersAvailable, NodeNotReadyError) as excp:
                    self.consumer_logger.info(f"Kafka message poll encountered the following exception: {excp}")
        else:
            raise TypeError("Consumer object is not initialized. Call create_consumer() first")

    def send_to_dlq(self, record, error: Exception, failure_category: str, retry_count: int = 0) -> None:
        """
        Send event and error encountered to DLQ topic.

        :param record: current record that was being processed that failed
        :param error: Exception error that was captured.
        :param failure_category: One of retryable_exhausted, non_retryable, or unexpected.
        :param retry_count: number of retries the system did before sending to DLQ.
        :return:
        """
        validator = OrderEventValidator(record.value)
        self.create_dlq_producer()
        dlq_message = {
            "failure_category": failure_category,
            "error_type": type(error).__name__,
            "retry_count": retry_count,
            "event_id": validator.event_id,
            "order_id": validator.order_id,
            "source": {
                "topic": record.topic,
                "partition": record.partition,
                "offset": record.offset,
            },
            "event": record.value,
            "error": str(error),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.dlq_producer.send(self.dlq_topic, value=dlq_message)
        self.dlq_producer.flush()
        self.consumer_logger.info(f"DLQ message sent to {self.dlq_topic}")

    def process_event_with_retries(self, order_event: dict) -> None:
        """
        Process an order with setup for retry controls.
        :param order_event:
        :return:
        """
        retry_count = 0

        while True:
            try:
                order_service = OrderService(order_event)
                order_service.process_order()
                return
            except RetryableProcessingError as exc:
                if retry_count >= self.max_retries:
                    self.consumer_logger.error(f"Retry attempts exhausted; sending to DLQ")
                    raise
                # Exponential backoff delay
                delay = 2 ** retry_count
                self.consumer_logger.warning(f"Retryable failure on attempt: {retry_count + 1} Retrying in {delay} seconds")
                sleep(delay)
                retry_count += 1