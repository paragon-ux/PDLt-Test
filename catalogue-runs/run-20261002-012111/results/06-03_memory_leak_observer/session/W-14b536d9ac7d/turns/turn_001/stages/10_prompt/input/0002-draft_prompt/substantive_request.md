TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
The request asks to analyse the provided Python observer pattern implementation for a memory leak caused by observers never being unsubscribed. Identify the leak, explain why the persistent reference to the DataProcessor.handle_data callback prevents the DataProcessor instance from being garbage‑collected, and fix the lifecycle by ensuring observers are removed (e.g., by adding an unsubscribe method or cleaning up in a destructor). Also provide a test that demonstrates the leak exists before the fix (using weakref or object counting) and that it is resolved after applying the fix. The code includes classes EventEmitter, DataProcessor, and function process_batch, with the event name 'data' used for subscription.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- EventEmitter
- on
- DataProcessor
- handle_data
- process_batch
- batch
- 'data'
