import copy


class MetricCollector(object):
    ORDERS_PROCESSED_SUCCESSFULLY = "orders_processed_successfully"
    DUPLICATE_EVENTS_DETECTED = "duplicate_events_detected"
    RETRY_ATTEMPTS_TOTAL = "retry_attempts_total"
    RETRY_EXHAUSTED_TOTAL = "retry_exhausted_total"
    ORDERS_SENT_TO_DLQ = "orders_sent_to_dlq"
    ORDERS_FAILED_RETRYABLE = "orders_failed_retryable"
    ORDERS_FAILED_NON_RETRYABLE = "orders_failed_non_retryable"

    def __init__(self):
        self.metrics_map = dict(
            orders_processed_successfully=0,  # total orders processed successfully
            duplicate_events_detected=0,  # total deplicate events detected and skipped processing
            retry_attempts_total=0,  # total retry attempts across all events
            retry_exhausted_total=0,  # retries fully exhausted
            orders_sent_to_dlq=0,  # event actually published to DLQ
            orders_failed_retryable=0,  # an event entered retryable failure handling
            orders_failed_non_retryable=0,  # total events that were not retryable
        )

    def increment(self, metric_name, amount=1):
        """
        For a given metric name that exists in the mapping increment its count by amount
        :param metric_name:
        :param amount:
        :return:
        """
        if metric_name in self.metrics_map.keys():
            self.metrics_map[metric_name] += amount
        else:
            raise KeyError(f"Metric {metric_name} does not exist")
        return

    def get(self, metric_name) -> int:
        """
        Retrieve the metric value by name
        :param metric_name:
        :return:
        """
        return self.metrics_map.get(metric_name)

    def snapshot(self) -> dict:
        """
        Returns a copy of the current metrics mapping
        :return:
        """
        return copy.copy(self.metrics_map)


    def reset(self):
        """
        Resets the current metrics mapping
        :return:
        """
        for metric_name in self.metrics_map.keys():
            self.metrics_map[metric_name] = 0
