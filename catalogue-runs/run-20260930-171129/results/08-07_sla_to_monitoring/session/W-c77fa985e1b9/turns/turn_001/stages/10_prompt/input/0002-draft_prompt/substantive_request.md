TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Extract concrete monitoring rules from the provided SLA document. For each SLA commitment, identify the metric to monitor, the alerting threshold, the measurement window, and produce a sample Prometheus-style alerting rule. The SLA commitments are: API uptime >= 99.9% measured monthly, read operation response time <= 200ms at the 95th percentile, write operation response time <= 500ms at the 95th percentile, error rate <= 0.1% of total requests, and planned maintenance windows max 4 hours/month excluded from uptime calculations with 48‑hour advance notification.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- monthly
- 200ms
- 95th percentile
- 500ms
- total requests
- 4 hours/month
- planned maintenance
