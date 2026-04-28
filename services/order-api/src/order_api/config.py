import os


class Config:
    KAFKA_BROKER = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "orders")
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    KAFKA_ENABLED = os.environ.get("KAFKA_ENABLED", True)
    DEBUG = os.environ.get("DEBUG", False)
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))


class LocalConfig(Config):
    HOST = os.environ.get("HOST", "localhost")
    DEBUG = os.environ.get("DEBUG", True)
    KAFKA_ENABLED = os.environ.get("KAFKA_ENABLED", False)
    USE_RELOADER = os.environ.get("USE_RELOADER", True)


class DevelopmentConfig(Config):
    pass


class QAConfig(Config):
    pass


class ProductionConfig(Config):
    pass