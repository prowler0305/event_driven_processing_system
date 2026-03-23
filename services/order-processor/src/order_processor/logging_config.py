# logging_config.py
import logging
from logging.config import dictConfig

class OrderContextFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "event_id"):
            record.event_id = "-"
        if not hasattr(record, "order_id"):
            record.order_id = "-"
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
                    '["event": "%(event_id)s", "order": "%(order_id)s"], '
                    '"message": "%(message)s"'
                    # '"group": "%(kafka_group)s", "topic": "%(kafka_topic)s", '
                    # '"partition": "%(kafka_partition)s", "offset": "%(kafka_offset)s"}'
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