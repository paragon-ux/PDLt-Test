- **Latency:** Batch incurs ~24 h + 45 min delay, unsuitable for near‑real‑time insights. Streaming can deliver results in seconds, enabling rapid response to user behavior.
- **Cost:** Batch runs a single 45‑minute job once per day, incurring compute only for that window. Streaming requires always‑on resources (e.g., stream processors, state stores), leading to higher continuous cost despite lower per‑job spend.
- **Complexity:** Batch pipelines are simpler – straightforward retry and re‑run logic. Streaming adds complexity: exactly‑once guarantees, watermarks, late‑data handling, and operational monitoring of continuous jobs.
- **Recommendation:** Prefer **batch processing** for this workload.
  - The daily freshness of downstream dashboards matches the batch latency, so the additional latency of streaming offers little business value.
  - Batch’s lower operational cost and simpler implementation align with the team’s likely resource constraints.
  - If near‑real‑time analytics become a requirement, a hybrid approach (batch for bulk reporting plus a lightweight stream for real‑time alerts) could be considered.

**Justification:** The batch mode satisfies the latency requirement (daily dashboards), minimizes cost by avoiding always‑on infrastructure, and reduces engineering complexity, making it the optimal choice for the current workload.
