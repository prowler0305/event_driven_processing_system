import logging
import tomllib
from pathlib import Path

logger = logging.getLogger(__name__)

class Config:
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

config = Config()