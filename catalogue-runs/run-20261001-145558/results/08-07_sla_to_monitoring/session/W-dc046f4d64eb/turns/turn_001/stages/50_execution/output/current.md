- SLA Commitment: API uptime ≥ 99.9% measured monthly
  Metric: api_uptime_ratio
  Threshold: 0.999
  Measurement Window: 30d
  Prometheus Rule: |
    ALERT ApiUptimeLow
    IF (sum_over_time(api_uptime_ratio[30d]) / 30) < 0.999
    FOR 5m
    LABELS {severity="critical"}
    ANNOTATIONS {summary="API uptime below 99.9%", description="The API uptime over the last month is below the SLA target."}

- SLA Commitment: Read operation response time ≤ 200 ms at the 95th percentile
  Metric: api_read_latency_seconds
  Threshold: 0.2
  Measurement Window: 5m
  Prometheus Rule: |
    ALERT ReadLatencyHigh
    IF histogram_quantile(0.95, sum(rate(api_read_latency_seconds_bucket[5m])) by (le)) > 0.2
    FOR 5m
    LABELS {severity="warning"}
    ANNOTATIONS {summary="Read latency exceeds 200 ms", description="95th‑percentile read latency over the last 5 minutes exceeds the SLA threshold."}

- SLA Commitment: Write operation response time ≤ 500 ms at the 95th percentile
  Metric: api_write_latency_seconds
  Threshold: 0.5
  Measurement Window: 5m
  Prometheus Rule: |
    ALERT WriteLatencyHigh
    IF histogram_quantile(0.95, sum(rate(api_write_latency_seconds_bucket[5m])) by (le)) > 0.5
    FOR 5m
    LABELS {severity="warning"}
    ANNOTATIONS {summary="Write latency exceeds 500 ms", description="95th‑percentile write latency over the last 5 minutes exceeds the SLA threshold."}

- SLA Commitment: Error rate ≤ 0.1% of total requests
  Metric: api_error_rate
  Threshold: 0.001
  Measurement Window: 5m
  Prometheus Rule: |
    ALERT HighErrorRate
    IF sum(rate(api_requests_total[5m])) > 0 AND (sum(rate(api_errors_total[5m])) / sum(rate(api_requests_total[5m]))) > 0.001
    FOR 5m
    LABELS {severity="critical"}
    ANNOTATIONS {summary="Error rate exceeds 0.1%", description="The error rate over the last 5 minutes exceeds the SLA limit."}
