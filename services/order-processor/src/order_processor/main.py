import logging

from order_processor.consumer import Consumer
from order_processor.logging_config import configure_logging
from order_processor.metrics.collector import MetricCollector

if __name__ == "__main__":
    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting order processor...")
        consumer = Consumer(metrics_collector_obj=MetricCollector())
        consumer.start()
    except Exception:
        logger.exception("Order processor crashed with exception:")