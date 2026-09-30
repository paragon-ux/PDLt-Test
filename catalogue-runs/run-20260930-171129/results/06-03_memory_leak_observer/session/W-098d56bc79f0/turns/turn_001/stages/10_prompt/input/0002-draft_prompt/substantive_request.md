TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify the memory leak caused by the EventEmitter observer pattern where DataProcessor instances are never unsubscribed, explain why the leak prevents garbage collection, and modify the code to manage the lifecycle of observers so that each DataProcessor unregisters its listener after processing. Provide a test that demonstrates the leak exists when process_batch is called many times and shows that memory usage stabilizes after applying the fix.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- EventEmitter
- on
- DataProcessor
- process_batch
- batch
