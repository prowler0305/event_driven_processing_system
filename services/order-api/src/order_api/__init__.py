import logging
import os

from flask import Flask
from order_api.blueprints.order_bp import orders_bp
from order_api.kafka_helpers.producer import close_kafka_producer


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(os.environ.get("APP_ENV_CONFIG"))
    app.logger.setLevel(logging.INFO)

    #Register blueprints
    app.register_blueprint(orders_bp, url_prefix="/api/v1")

    # register kafka producer cleanup
    app.teardown_appcontext(close_kafka_producer)

    return app