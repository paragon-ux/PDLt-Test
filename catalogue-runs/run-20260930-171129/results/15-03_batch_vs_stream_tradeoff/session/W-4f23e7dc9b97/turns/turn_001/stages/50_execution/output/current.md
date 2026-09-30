Latency Trade‑off:
- Batch: runs once per night, delivering results after a 24 h window plus ~45 min processing time (≈24 h 45 min latency). Data is only available to downstream dashboards once per day.
- Stream: processes events as they arrive, typically delivering results within seconds to a few minutes, enabling near‑real‑time dashboards and rapid anomaly detection.

Cost Trade‑off:
- Batch: incurs cost of a single large compute job each night (e.g., one big Spark/MapReduce cluster). Idle resources for the rest of the day are not billed.
- Stream: requires always‑on infrastructure (e.g., a small cluster or managed streaming service) that runs 24/7. Even at modest utilization, the hourly cost accumulates to a higher daily spend than a single nightly job, though the exact amount depends on the chosen service and scaling.

Complexity Trade‑off:
- Batch: simple retry semantics; if the nightly job fails, it can be re‑run. No need for exactly‑once guarantees, watermarks, or late‑data handling.
- Stream: must implement exactly‑once processing, manage watermarks, handle out‑of‑order and late events, and ensure fault‑tolerant state management. This adds operational overhead and requires more sophisticated monitoring and testing.

Recommendation:
Given the business context—clickstream data feeding dashboards that currently refresh only once per day—the batch approach already meets the latency requirement. Switching to streaming would provide real‑time insights but at higher infrastructure cost and operational complexity. If the organization does not need sub‑hourly analytics and wants to keep operational overhead low, the nightly batch processing remains the preferred solution. However, if near‑real‑time monitoring (e.g., fraud detection, rapid UI personalization) becomes a priority, the added cost and complexity of streaming may be justified. In the present scenario, **continue with the nightly batch approach** and revisit streaming only if real‑time use cases emerge.

---
Result IR follows.
