# logging_config.py
import logging
from logging.config import dictConfig

class OrderContextFilter(logging.Filter):
    def filter(self, record):
        filter_fields = [
            "order_id",
            "event_id",
            "kafka_groups",
            "kafka_topic",
            "kafka_offset",
            "kafka_partition",
            "retry_count",
            "error_type",
            "failure_category"
        ]
        for field in filter_fields:
            if not hasattr(record, field):
                setattr(record, field, "-")
        return True

def configure_logging():
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "order_context": {
                "()": "order_processor.logging_config.OrderContextFilter"
            }
        },
        "formatters": {
            "json": {
                "format": (
                    '{"time": "%(asctime)s", "level": "%(levelname)s", '
                    '"logger": "%(name)s", "lineno": "%(lineno)d", '
                    '["event": "%(event_id)s", "order": "%(order_id)s", '
                    '"group": "%(kafka_group)s", "topic": "%(kafka_topic)s", '
                    '"partition": "%(kafka_partition)s", "offset": "%(kafka_offset)s"'
                    '"retry_count": "%(retry_count)d", "error_type": "%(error_type)s", "failure_category": "%(failure_category)s"]}'
                    '"message": "%(message)s"'

                )
            }
        },

        "handlers": {
            # "queue": {
            #     "class": "logging.handlers.QueueHandler",
            #     "queue": "ext://queue.Queue()"
            # },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["order_context"],
                "level": "INFO"
            }
        },

        "loggers": {
            "": {  # root logger
                "handlers": ["console"],
                "level": "INFO",
                "propagate": True
            }
        }
    })