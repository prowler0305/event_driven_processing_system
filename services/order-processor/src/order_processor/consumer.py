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
            except KafkaConfigurationError as kafka_configuration_error:
                logger.exception(f"KafkaConsumer object can't be created due to configuration error")
                raise kafka_configuration_error

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
                            record_logger = logger
                            try:
                                validator = OrderEventValidator(order_event)
                                event_id = validator.event_id
                                record_logger = self.build_log_adapter(record, event_id)
                                if event_id in self.processed_events:
                                    raise DuplicateEventError()
                                self.process_event_with_retries(order_event)
                                self.processed_events.add(event_id)
                                self.consumer.commit()
                                record_logger.info("Order committed")
                            except DuplicateEventError:
                                record_logger.info(f"Duplicate event detected: {event_id} - skipping")
                                self.consumer.commit() # Commit this duplicate offset so we don't process forever.
                                continue
                            except RetryableProcessingError as exc:
                                self.send_to_dlq(record, exc, failure_category="retryable_exhausted", retry_count=self.max_retries)
                                self.consumer.commit()
                            except NonRetryableProcessingError as exc:
                                record_logger.error(f"Non-retryable processing failure: {str(exc)}")
                                self.send_to_dlq(record, exc, failure_category="non_retryable")
                                self.consumer.commit()
                            except Exception as exc:
                                record_logger.exception("Unexpected processing failure")
                                # send this to DLQ topic.
                                self.send_to_dlq(record, exc, failure_category="unexpected")
                                self.consumer.commit()

                except (KafkaTimeoutError, KafkaConnectionError, NoBrokersAvailable, NodeNotReadyError) as excp:
                    logger.error(f"Kafka message poll encountered the following exception: {excp}")
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
        record_logger = self.build_log_adapter(record, validator.event_id)
        self.create_dlq_producer()
        error_type = type(error).__name__
        log_ctx = dict(error_type=error_type, retry_count=retry_count, failure_category=failure_category)
        dlq_message = {
            "failure_category": failure_category,
            "error_type": error_type,
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
        dlq_logger = logging.LoggerAdapter(logger=record_logger, extra=log_ctx, merge_extra=True)
        dlq_logger.info(f"DLQ message sent to {self.dlq_topic}")

    def process_event_with_retries(self, order_event: dict, record_logger: logging.LoggerAdapter) -> None:
        """
        Process an order with setup for retry controls.
        :param order_event:
        :param record_logger: existing record level base logging adapter.
        :return:
        """
        retry_count = 0
        failure_category = "retryable"
        log_ctx = dict(failure_category=failure_category, retry_count=retry_count)
        while True:
            try:
                order_service = OrderService(order_event)
                order_service.process_order()
                return
            except RetryableProcessingError as exc:
                log_ctx["error_type"] = type(exc).__name__
                log_ctx["retry_count"] = retry_count
                if retry_count >= self.max_retries:
                    log_ctx["failure_category"] = "retryable_exhausted"
                    exhaustion_logger = logging.LoggerAdapter(logger=record_logger, extra=log_ctx, merge_extra=True)
                    exhaustion_logger.error(f"Retry attempts exhausted with failure {str(exc)}; sending to DLQ")
                    raise
                # Exponential backoff delay
                delay = 2 ** retry_count
                retry_logger = logging.LoggerAdapter(logger=record_logger, extra=log_ctx, merge_extra=True)
                retry_logger.warning(f"Retryable failure {str(exc)}, on attempt: {retry_count + 1} Retrying in {delay} seconds")
                sleep(delay)
                retry_count += 1

    def build_log_adapter(self, record, event_id) -> logging.LoggerAdapter:
        """
        Build a logging.LogAdapter context by adding:

        * event_id
        * topic
        * partition
        * offset

        :param record:
        :param event_id:
        :return:
        """
        log_ctx = dict(
            event_id=event_id,
            topic=record.topic,
            partition=record.partition,
            offset=record.offset,
            group_id=self.group_id
        )
        return logging.LoggerAdapter(logger=logger, extra=log_ctx, merge_extra=True)
