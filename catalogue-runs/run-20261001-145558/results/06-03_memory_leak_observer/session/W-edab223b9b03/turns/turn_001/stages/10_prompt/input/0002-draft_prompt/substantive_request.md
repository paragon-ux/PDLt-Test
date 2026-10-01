TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify the memory leak caused by EventEmitter observers never being unsubscribed when DataProcessor instances are discarded. Explain why the persistent listeners prevent garbage collection of DataProcessor objects. Modify the implementation so that each DataProcessor removes its listener after use, ensuring no lingering references. Provide a test that demonstrates the leak exists before the fix (e.g., by tracking object count or memory usage over many calls to process_batch) and shows the leak is resolved after applying the fix.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- EventEmitter
- DataProcessor
- process_batch
- on
- batch
- memory leak
