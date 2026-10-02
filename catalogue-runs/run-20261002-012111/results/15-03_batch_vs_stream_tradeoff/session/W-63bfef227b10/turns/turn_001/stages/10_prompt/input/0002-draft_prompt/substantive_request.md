TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Analyze the latency tradeoff (batch processing of 24 hours plus 45 minutes vs stream processing with seconds-level latency), the cost tradeoff (batch: single nightly compute job vs stream: always‑on infrastructure), and the complexity tradeoff (batch: simple retry handling vs stream: exactly‑once semantics, watermarks, late‑data handling) for a clickstream data pipeline that currently processes 50 million events per day (~600 events/second average, 3000 events/second peak) with events averaging 500 bytes, using a nightly MapReduce batch job that takes 45 minutes, and downstream dashboards that refresh once per day. Provide a recommendation with justification on which approach to adopt.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- 50 million events per day
- ~600 events/second average
- 3000 events/second peak
- 45 minutes
- MapReduce
- stream processing
- once per day
