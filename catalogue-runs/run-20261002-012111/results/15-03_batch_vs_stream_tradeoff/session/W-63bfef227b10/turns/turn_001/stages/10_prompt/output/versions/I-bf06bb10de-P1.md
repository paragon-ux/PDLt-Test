ANALYZE latency tradeoff between batch processing of 24 hours plus 45 minutes and stream processing with seconds-level latency
ANALYZE cost tradeoff between batch processing (single nightly compute job) and stream processing (always‑on infrastructure)
ANALYZE complexity tradeoff between batch processing (simple retry handling) and stream processing (exactly‑once semantics, watermarks, late-data handling)
FOR the clickstream data pipeline that processes:
- 50 million events per day
- ~600 events/second average
- 3000 events/second peak
with events averaging 500 bytes, using a nightly MapReduce batch job that takes 45 minutes, and downstream dashboards that refresh once per day
PROVIDE a recommendation with justification on which approach to adopt
