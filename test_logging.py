import logging

from order_processor.logging_config import configure_logging

if __name__ == "__main__":
    configure_logging()

    # Do some bast logging to test different levels and format types with basic fields
    plain_logger = logging.getLogger("plain_logger")
    plain_logger.setLevel(logging.DEBUG)  # Set to DEBUG
    plain_logger.debug("Testing a debug message")
    plain_logger.info("Testing an info message")
    plain_logger.warning("Testing a warning message")
    plain_logger.error("Testing an error message")
    plain_logger.critical("Testing a critical message")

    # Do some logging with a LoggerAdapter with some fake context fields
    ctx = dict(
        event_id="123",
        order_id="456",
        topic="log_testing",
        group_id="log_testing_group",
        partition=1,
        offset=23
    )
    context_base_logger = logging.getLogger("context_logger")
    context_logger = logging.LoggerAdapter(context_base_logger, extra=ctx, merge_extra=True)
    context_logger.setLevel(logging.DEBUG)  # Set to DEBUG
    context_logger.debug("Testing a debug message")
    context_logger.info("Testing an info message")
    context_logger.warning("Testing a warning message")
    context_logger.error("Testing an error message")
    context_logger.critical("Testing a critical message")


    # Do some exception generation to test exception context fields added.
    excp_ctx = dict(failure_category="testing_failure", retry_count=0, error_type=None)

    try:
        causes_excp = excp_ctx["non_existing_key"]
    except KeyError as kerr:
        exception_logger = logging.LoggerAdapter(context_logger, extra=excp_ctx, merge_extra=True)
        excp_ctx["error_type"] = type(kerr).__name__
        exception_logger.exception(f"Testing logging an exception")

