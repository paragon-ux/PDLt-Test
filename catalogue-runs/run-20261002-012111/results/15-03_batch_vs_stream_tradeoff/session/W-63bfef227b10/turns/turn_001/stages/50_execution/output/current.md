**Latency trade‑off**
- *Batch*: Data is processed once per day. End‑to‑end latency is roughly 24 h + 45 min (the time until the nightly MapReduce job finishes). Dashboard consumers see data only after the daily refresh, so the information is stale by up to a day.
- *Stream*: Each event is ingested and processed within seconds (typical streaming frameworks give sub‑second to low‑second latency). Dashboards can be refreshed continuously or near‑real‑time, reducing data staleness to seconds.

**Cost trade‑off**
- *Batch*: A single nightly compute job runs on a fixed‑size cluster (e.g., a few mappers/reducers). Compute resources are idle the rest of the day, so you pay only for the job duration (45 min) plus any storage I/O. For 50 M events × 500 B ≈ 25 GB of raw data, the cost is modest and predictable.
- *Stream*: Requires an always‑on cluster (or managed service) that processes ~3000 events/s peak ⇒ ~1.5 GB/h of ingest bandwidth and roughly 36 GB per day. The cluster must be provisioned for peak load, meaning higher hourly resource usage. Costs are therefore roughly 24 h × (continuous‑run instance price) which is usually several‑fold higher than a nightly batch job, although managed services can amortize operational overhead.

**Complexity trade‑off**
- *Batch*: Simpler architecture. Retry logic is limited to re‑running the nightly job; data ordering, exactly‑once guarantees, and late‑data handling are naturally covered by the batch window. Implementation and operational burden are low.
- *Stream*: Requires handling of exactly‑once semantics, watermark management, out‑of‑order and late events, and stateful processing. The code base is more intricate, operational monitoring (e.g., lag, checkpointing) is required, and debugging is harder. This adds significant development and ops complexity.

**Recommendation**
Given the workload (50 M events/day, modest peak of 3000 events/s) and the downstream requirement of a once‑daily dashboard, the batch approach already meets the business need with lower cost and lower operational complexity. The latency benefit of streaming (seconds‑level) is not needed for a daily dashboard and would incur substantially higher infrastructure spend and engineering effort.

**Conclusion**: Stick with the nightly batch MapReduce job. If a future requirement emerges for near‑real‑time analytics or tighter SLAs, a migration to streaming can be revisited, but today the batch solution offers the best cost‑to‑benefit ratio.
