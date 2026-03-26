import logging
import json


class JsonFormatter(logging.Formatter):
    OPTIONAL_FIELDS = [
        "event_id",
        "order_id",
        "topic",
        "group_id",
        "partition",
        "offset",
        "failure_category",
        "retry_count",
        "error_type"
    ]
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.OPTIONAL_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                log_data[field] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ColorFormatter(logging.Formatter):
    COLORS = dict(
        DEBUG="\033[36m",  # cyan
        INFO="\033[32m",  # green
        WARNING="\033[33m",  # yellow
        ERROR="\033[31m",  # red
        CRITICAL="\033[31;1m",  # bold red
    )
    RESET = "\033[0m"  # reset

    def format(self, record):
        formatted_output = super().format(record)
        color_seq = self.COLORS.get(record.levelname, "")
        return f"{color_seq}{formatted_output}{self.RESET}"