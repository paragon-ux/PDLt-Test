# Prometheus alerting rules generated from the SLA commitments

# Rule file: sla_alerts.yml

groups:
  - name: sla_alerts
    rules:
      # R1: 99.9% uptime measured monthly (excluding planned maintenance)
      - alert: SLA_UptimeViolation
        expr: |
          1 - (sum_over_time(up{job="api"}[30d]) / sum_over_time(up{job="api"}[30d])) > 0.001
        for: 30d
        labels:
          severity: critical
        annotations:
          summary: "API uptime below 99.9% for the month"
          description: "The API has an uptime of less than 99.9% over the past month."

      # R2: Read operation latency ≤200ms at the 95th percentile
      - alert: SLA_ReadLatencyViolation
        expr: |
          histogram_quantile(0.95, sum by (le) (rate(api_read_request_duration_seconds_bucket[5m]))) > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Read latency exceeds 200ms at 95th percentile"
          description: "Read operation 95th percentile latency > 200ms."

      # R3: Write operation latency ≤500ms at the 95th percentile
      - alert: SLA_WriteLatencyViolation
        expr: |
          histogram_quantile(0.95, sum by (le) (rate(api_write_request_duration_seconds_bucket[5m]))) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Write latency exceeds 500ms at 95th percentile"
          description: "Write operation 95th percentile latency > 500ms."

      # R4: Error rate ≤0.1% of total requests
      - alert: SLA_ErrorRateViolation
        expr: |
          (sum(rate(api_requests_total{status=~"5.."}[5m])) / sum(rate(api_requests_total[5m]))) > 0.001
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate exceeds 0.1% of total requests"
          description: "Error rate > 0.1% over the past 5 minutes."
