PARSE the provided SLA document
FOR EACH SLA commitment
IDENTIFY the metric to monitor
IDENTIFY the alerting threshold
IDENTIFY the measurement window
MAP any referenced operative task entities (monthly, 200ms, 95th percentile, 500ms, total requests, 4 hours/month, planned maintenance) to the extracted elements
CONSTRUCT a Prometheus‑style alerting rule using the identified metric, threshold, and window
EMIT the set of generated Prometheus‑style alerting rules
