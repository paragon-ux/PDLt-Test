TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the issue based on the provided Python GC log showing periodic latency spikes. Explain why generation 2 collections are becoming slower, interpret the growing object count in generation 2, list three common code patterns that can cause such behaviour, and provide tuning recommendations using gc.set_threshold, gc.freeze, or gc.disable for specific operations.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- gc.set_threshold
- gc.freeze
- gc.disable
