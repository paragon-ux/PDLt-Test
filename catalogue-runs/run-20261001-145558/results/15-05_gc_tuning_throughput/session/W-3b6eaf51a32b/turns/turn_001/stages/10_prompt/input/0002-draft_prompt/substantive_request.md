TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the Python GC log showing periodic latency spikes by explaining why generation 2 collections are getting slower, what the growing object count in generation 2 indicates, three specific code patterns that commonly cause this behavior, and provide tuning recommendations involving gc.set_threshold, gc.freeze, or gc.disable for specific operations.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- gc.set_threshold
- gc.freeze
- gc.disable
