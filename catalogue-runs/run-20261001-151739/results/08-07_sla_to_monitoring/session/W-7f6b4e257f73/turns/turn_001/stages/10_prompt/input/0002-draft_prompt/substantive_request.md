TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
User requests extraction of concrete monitoring rules for each SLA commitment. Specifically, produce the metric to monitor, the alerting threshold, the measurement window, and a sample Prometheus-style alerting rule. The SLA commitments are: 99.9% uptime measured monthly, response time for read operations ≤ 200ms at the 95th percentile, response time for write operations ≤ 500ms at the 95th percentile, error rate ≤ 0.1% of total requests, and planned maintenance windows limited to max 4 hours/month (excluded from uptime). Additionally, customers must be notified 48 hours before planned maintenance. The task requires generating monitoring definitions, thresholds, windows, and example Prometheus alert expressions for each.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- 99.9% uptime
- 200ms
- 95th percentile
- 500ms
- 0.1%
- max 4 hours/month
- 48 hours
- read operations
- write operations
