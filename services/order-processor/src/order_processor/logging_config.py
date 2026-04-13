# logging_config.py
import logging
from logging.config import dictConfig

import logging_formatters
from order_processor.config.config import config


class OrderContextFilter(logging.Filter):
    def filter(self, record):
        filter_fields = [
            "order_id",
            "event_id",
            "group",
            "topic",
            "offset",
            "partition",
            "retry_count",
            "error_type",
            "failure_category"
        ]
        # for field in filter_fields:
        #     if not hasattr(record, field):
        #         setattr(record, field, "-")
        return True

def configure_logging():

    text_format = "%(asctime)s | %(levelname)s | %(name)s | %(lineno)d | %(message)s"
    if config.logging_format not in {"json", "text"}:
        raise ValueError(f"Invalid logging format: {config.logging_format}")

    selected_formatter = "color_text" if config.logging_enable_color else config.logging_format

    logger_config = {
        "version": 1,
        "disable_existing_loggers": False,
        # "filters": {
        #     "order_context": {
        #         "()": "order_processor.logging_config.OrderContextFilter"
        #     }
        # },
        "formatters": {
            "text": {
                "format": text_format
            },
            "json": {
                "()": logging_formatters.JsonFormatter
            },
            "color_text": {
                "()": logging_formatters.ColorFormatter,
                "fmt": text_format,
            }
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": selected_formatter,
                # "filters": ["order_context"],
                "level": config.logging_level
            }
        },

        "loggers": {
            "": {  # root logger
                "handlers": ["console"],
                "level": config.logging_level,
                "propagate": True
            },
            "kafka": {
                "level": config.kafka_logging_level,
                "handlers": ["console"],
                "propagate": False
            }
        }
    }

    dictConfig(logger_config)