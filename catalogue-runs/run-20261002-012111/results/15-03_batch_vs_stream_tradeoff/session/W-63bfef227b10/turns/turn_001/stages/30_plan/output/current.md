EXTRACT pipeline characteristics (50M events per day, ~600 events/second average, 3000 events/second peak, 500-byte events, nightly MapReduce job 45 minutes, dashboard refresh once per day)
ANALYZE latency tradeoff between batch processing (24h + 45min) and stream processing (seconds-level latency)
ANALYZE cost tradeoff between batch processing (single nightly compute job) and stream processing (always-on infrastructure)
ANALYZE complexity tradeoff between batch processing (simple retry handling) and stream processing (exactly-once semantics, watermarks, late-data handling)
COMPARE the latency, cost, and complexity analyses for the clickstream pipeline
SYNTHESIZE the comparison into a recommendation with justification
EMIT the recommendation and justification
