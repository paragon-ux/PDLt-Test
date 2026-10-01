READ the characteristics of the data pipeline: clickstream events 50 million per day, average 600 events/second, peak 3000 events/second, average event size 500 bytes, batch job duration 45 minutes, downstream dashboards refresh daily.
COMPARE latency tradeoff between batch processing (24‑hour window + 45‑minute job) and streaming processing (seconds‑scale latency).
COMPARE cost tradeoff between batch processing (single large compute job) and streaming processing (always‑on infrastructure).
COMPARE complexity tradeoff between batch processing (simple retry logic) and streaming processing (exactly‑once processing, watermarks, handling late data).
EVALUATE the impact of these tradeoffs on the given workload and operational requirements.
PROVIDE a recommendation stating which processing mode (batch or stream) is preferable for this pipeline.
JUSTIFY the recommendation by referencing the latency, cost, and complexity analyses.
OUTPUT the recommendation and justification in concise, bullet‑point form.
