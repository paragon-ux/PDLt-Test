**Latency.** Batch: an event can be up to 24 h old when the job starts, plus 45 min of processing, so ~24 h 45 min worst case. Streaming: seconds. But dashboards refresh daily, so today no consumer benefits from fresher data.

**Cost.** Volume: 50M × 500 B = 25 GB/day; average 600 ev/s ≈ 0.3 MB/s, peak 3,000 ev/s ≈ 1.5 MB/s. Batch: one cluster for 45 min/day (~3% utilization of a day). Streaming: brokers + stream processors running 24/7, sized for the 5× peak, plus state stores; typically several times the batch compute cost for this volume.

**Complexity.** Streaming needs exactly-once semantics (or idempotent sinks), event-time windows with watermarks, a late-data policy, checkpointed state, schema evolution in-flight, and on-call for an always-on system. Batch: rerun the job on failure; reprocessing is trivial.

**Recommendation.** Keep batch while the dashboards are daily. If fresher dashboards are wanted, move to hourly micro-batches first (cheap, same code). Adopt streaming only when a real-time consumer (alerting, personalization) justifies the cost and complexity.
