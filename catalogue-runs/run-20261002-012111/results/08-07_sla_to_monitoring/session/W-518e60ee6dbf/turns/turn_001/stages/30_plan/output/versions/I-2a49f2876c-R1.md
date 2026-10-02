READ the SLA document
FOR EACH SLA commitment DO
  IF commitment is 99.9% monthly uptime THEN
    IDENTIFY the metric to monitor as monthly uptime percentage
    SET the alerting threshold to less than 99.9% uptime
    DEFINE the measurement window as one calendar month
    GENERATE a sample Prometheus‑style alerting rule for uptime
  ENDIF
  IF commitment is read latency ≤200ms at the 95th percentile THEN
    IDENTIFY the metric to monitor as read latency at the 95th percentile
    SET the alerting threshold to greater than 200ms
    DEFINE the measurement window appropriate for latency measurement
    GENERATE a sample Prometheus‑style alerting rule for read latency
  ENDIF
  IF commitment is write latency ≤500ms at the 95th percentile THEN
    IDENTIFY the metric to monitor as write latency at the 95th percentile
    SET the alerting threshold to greater than 500ms
    DEFINE the measurement window appropriate for latency measurement
    GENERATE a sample Prometheus‑style alerting rule for write latency
  ENDIF
  IF commitment is error rate ≤0.1% of total requests THEN
    IDENTIFY the metric to monitor as error rate percentage of total requests
    SET the alerting threshold to greater than 0.1% error rate
    DEFINE the measurement window appropriate for error rate calculation
    GENERATE a sample Prometheus‑style alerting rule for error rate
  ENDIF
  IF commitment is maintenance windows up to 4 hours per month excluded from uptime calculations THEN
    IDENTIFY the metric to monitor as effective uptime excluding maintenance windows
    SET the alerting threshold to less than 99.9% effective uptime
    DEFINE the measurement window as one calendar month, excluding up to 4 hours of maintenance per month
    GENERATE a sample Prometheus‑style alerting rule for effective uptime
  ENDIF
  IF commitment is 48‑hour prior customer notification requirement THEN
    IDENTIFY the metric to monitor as notification compliance timing
    SET the alerting threshold to notification sent later than 48 hours before required event
    DEFINE the measurement window appropriate for tracking notifications
    GENERATE a sample Prometheus‑style alerting rule for notification compliance
  ENDIF
END FOR
