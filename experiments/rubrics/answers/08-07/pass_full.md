| Commitment | Metric | Threshold | Window |
|---|---|---|---|
| 99.9% monthly uptime (excl. maintenance) | probe success / successful requests, maintenance excluded | < 99.9% → budget 43.2 min per 30 days | rolling 30 d; burn-rate alerts on 1 h and 6 h |
| Read p95 ≤ 200 ms | `http_request_duration_seconds` histogram, `method="GET"` | p95 > 0.2 s | 5 m, for 10 m |
| Write p95 ≤ 500 ms | same, `method=~"POST|PUT|PATCH|DELETE"` | p95 > 0.5 s | 5 m, for 10 m |
| Errors ≤ 0.1% | 5xx / all requests | > 0.001 | 5 m, for 10 m; 30 d for the SLA report |

```yaml
groups:
- name: sla
  rules:
  - alert: ErrorBudgetFastBurn        # 14.4x burn: 2% of the monthly budget in 1h
    expr: (1 - avg_over_time(probe_success{job="api"}[1h]) unless on() maintenance_window == 1) > 14.4 * 0.001
    for: 2m
  - alert: ReadLatencyP95High
    expr: histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{method="GET"}[5m]))) > 0.2
    for: 10m
  - alert: WriteLatencyP95High
    expr: histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{method=~"POST|PUT|PATCH|DELETE"}[5m]))) > 0.5
    for: 10m
  - alert: ErrorRateHigh
    expr: sum(rate(http_requests_total{code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.001
    for: 10m
```
Maintenance windows are recorded as a `maintenance_window` metric (or silences) so they are excluded from uptime. The 48-hour notice is a process requirement: check the change calendar for windows scheduled less than 48 h ahead, not a metric.
