IDENTIFY the memory leak in the EventEmitter/DataProcessor implementation where DataProcessor instances remain referenced via listeners, preventing garbage collection.
EXPLAIN why the listeners added via the on method for the 'data' event keep DataProcessor instances alive.
MODIFY the code to unsubscribe the DataProcessor's listener after processing completes (or use weak references) so that each DataProcessor can be collected after process_batch finishes.
PROVIDE a test that demonstrates the memory leak exists before the fix by measuring increased object count after repeated calls to process_batch.
PROVIDE a test that demonstrates the leak is resolved after applying the fix, showing no increase in object count after repeated calls.
PRESERVE the literal identifiers EventEmitter, DataProcessor, process_batch, on, and data.
