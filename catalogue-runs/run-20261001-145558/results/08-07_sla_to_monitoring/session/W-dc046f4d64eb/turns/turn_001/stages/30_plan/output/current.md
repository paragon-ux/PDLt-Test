READ the provided SLA document
FOR EACH SLA commitment DO
    IDENTIFY the monitoring metric
    IDENTIFY the alerting threshold
    IDENTIFY the measurement window
    CREATE a sample Prometheus-style alerting rule representing the metric, threshold, and window
    RECORD an entry containing the commitment description, the metric, the threshold, the measurement window, and the generated rule
END FOR
OUTPUT the compiled list of entries
