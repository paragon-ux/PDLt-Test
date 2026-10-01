TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify and explain the memory leak in the provided EventEmitter/DataProcessor implementation where DataProcessor instances remain referenced via listeners, preventing garbage collection. Modify the code to unsubscribe the DataProcessor's listener (or use weak references) after processing so that each DataProcessor can be collected after process_batch completes. Provide a test that demonstrates the leak exists before the fix (e.g., measuring increased object count after repeated calls) and shows that the leak is resolved after applying the fix. Preserve literal identifiers such as EventEmitter, DataProcessor, process_batch, and the event name 'data'.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- EventEmitter
- DataProcessor
- process_batch
- on
- data
