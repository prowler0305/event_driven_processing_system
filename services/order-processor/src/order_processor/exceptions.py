class DuplicateEventError(Exception):
    pass


class RetryableProcessingError(Exception):
    pass


class NonRetryableProcessingError(Exception):
    pass

