# Alert rule for 99.9% uptime (monthly)
# Metric: percentage of uptime over a month (excluding planned maintenance)
# Threshold: uptime < 99.9%
# Measurement window: 1 month
ALERT UptimeLow
  IF (1 - avg_over_time(up_time_ratio[30d])) > 0.001
  FOR 5m
  ANNOTATIONS {
    summary = "Uptime below 99.9%",
    description = "The service uptime over the last month fell below the SLA commitment of 99.9% uptime."
  }

# Alert rule for read operation latency ≤ 200ms at the 95th percentile
# Metric: 95th percentile of read latency
# Threshold: > 200ms
# Measurement window: 5 minutes
ALERT ReadLatencyHigh
  IF histogram_quantile(0.95, sum(rate(api_read_latency_seconds_bucket[5m])) by (le)) > 0.2
  FOR 5m
  ANNOTATIONS {
    summary = "Read latency exceeds 200ms at the 95th percentile",
    description = "Read operations latency 95th percentile is above 200ms."
  }

# Alert rule for write operation latency ≤ 500ms at the 95th percentile
# Metric: 95th percentile of write latency
# Threshold: > 500ms
# Measurement window: 5 minutes
ALERT WriteLatencyHigh
  IF histogram_quantile(0.95, sum(rate(api_write_latency_seconds_bucket[5m])) by (le)) > 0.5
  FOR 5m
  ANNOTATIONS {
    summary = "Write latency exceeds 500ms at the 95th percentile",
    description = "Write operations latency 95th percentile is above 500ms."
  }

# Alert rule for error rate ≤ 0.1% of total requests
# Metric: error rate
# Threshold: > 0.1%
# Measurement window: 5 minutes
ALERT ErrorRateHigh
  IF (sum(rate(errors_total[5m])) / sum(rate(requests_total[5m]))) > 0.001
  FOR 5m
  ANNOTATIONS {
    summary = "Error rate exceeds 0.1%",
    description = "Observed error rate is above the SLA threshold of 0.1% of total requests."
  }

# Alert rule for planned maintenance windows limited to max 4 hours/month
# Metric: total planned maintenance duration per month
# Threshold: > 4 hours
# Measurement window: 1 month
ALERT MaintenanceDurationHigh
  IF sum_over_time(planned_maintenance_seconds[30d]) > 14400
  FOR 5m
  ANNOTATIONS {
    summary = "Planned maintenance exceeds max 4 hours/month",
    description = "Planned maintenance duration in the last month exceeded the SLA limit of max 4 hours/month."
  }

# Alert rule for customer notification 48 hours before planned maintenance
# Metric: time between notification and start of maintenance
# Threshold: < 48 hours before maintenance
# Measurement window: check each scheduled maintenance event
ALERT MaintenanceNotificationLate
  IF time() - maintenance_notification_timestamp > 172800
  FOR 5m
  ANNOTATIONS {
    summary = "Maintenance notification less than 48 hours before start",
    description = "Customers were not notified at least 48 hours before the planned maintenance."
  }
