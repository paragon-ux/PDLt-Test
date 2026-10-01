TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify the memory leak in the provided Python observer pattern implementation where EventEmitter retains references to DataProcessor instances via the on('data', ...) subscription, preventing garbage collection when process_batch is invoked thousands of times. Explain why this lingering listener stops the DataProcessor objects from being collected. Provide a corrected implementation that unsubscribes the DataProcessor's handle_data callback after the batch processing (e.g., by removing the listener or using a context manager). Include a test that demonstrates the leak before the fix (using weakref or similar to show DataProcessor instances remain alive after process_batch) and verifies that the leak is resolved after applying the fix.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- EventEmitter
- DataProcessor
- process_batch
- handle_data
- on
- data
- thousands
