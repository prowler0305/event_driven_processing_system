import logging
import tomllib
from pathlib import Path

logger = logging.getLogger(__name__)

class Config:
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.toml"

        with open(config_path, "rb") as f:
            self._config = tomllib.load(f)

    @property
    def kafka_bootstrap_servers(self):
        return self._config["kafka"]["bootstrap_servers"]

    @property
    def orders_topic(self):
        return self._config["kafka"]["orders_topic"]

    @property
    def dlq_topic(self):
        return self._config["kafka"]["dlq_topic"]

    @property
    def consumer_group(self):
        return self._config["consumer"]["group_id"]

    @property
    def auto_offset_reset(self):
        return self._config["consumer"]["auto_offset_reset"]

    @property
    def poll_timeout_ms(self):
        return self._config["consumer"]["poll_timeout_ms"]

    @property
    def max_retries(self):
        return self._config["consumer"]["max_retries"]

    @property
    def connection_retries(self):
        return self._config["consumer"].get("connection_retries", 10)

    @property
    def connection_wait(self):
        return self._config["consumer"].get("connection_wait", 3)

    @property
    def logging_format(self):
        return self._config["logging"]["format"].lower()

    @property
    def logging_enable_color(self):
        return self._config["logging"]["enable_color"]

    @property
    def logging_level(self):
        log_level = self._config["logging"].get("level", "INFO").upper()
        if log_level not in Config.VALID_LOG_LEVELS:
            raise ValueError(f"Invalid logging level: {log_level}. Must be one of {Config.VALID_LOG_LEVELS}")
        return log_level

    @property
    def kafka_logging_level(self):
        log_level = self._config["logging"].get("kafka_log_level", "WARNING").upper()
        if log_level not in Config.VALID_LOG_LEVELS:
            raise ValueError(f"Invalid logging level for kafka_log_level setting: {log_level}. Must be one of {Config.VALID_LOG_LEVELS}")
        return log_level

config = Config()