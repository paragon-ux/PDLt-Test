ANALYZE the provided Python observer pattern implementation for a memory leak caused by observers never being unsubscribed.

IDENTIFY the leak.

EXPLAIN why the persistent reference to the DataProcessor.handle_data callback prevents the DataProcessor instance from being garbage‑collected.

FIX the lifecycle by ensuring observers are removed, e.g., add an unsubscribe method to EventEmitter or clean up in a destructor of DataProcessor.

PROVIDE a test that demonstrates the leak exists before the fix (using weakref or object counting) and that it is resolved after applying the fix.

VERBATIMLY LIST the OPERATIVE TASK ENTITIES: EventEmitter, on, DataProcessor, handle_data, process_batch, batch, 'data'.
