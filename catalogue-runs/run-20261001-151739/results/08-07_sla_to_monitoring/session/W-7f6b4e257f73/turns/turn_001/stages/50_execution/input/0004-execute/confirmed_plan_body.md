READ the SLA commitments
FOR each SLA commitment DO
    IDENTIFY the metric to monitor
    SPECIFY the alerting threshold as per the SLA
    SPECIFY the measurement window appropriate for the metric
    GENERATE a sample Prometheus‑style alert rule that fires when the threshold is breached
ENDFOR
VERIFY that each generated alert rule includes the required entity strings "99.9% uptime", "200ms", "95th percentile", "500ms", "0.1%", "max 4 hours/month", "48 hours", "read operations", "write operations"
ASSEMBLE the alert rules
EMIT the alert rules
