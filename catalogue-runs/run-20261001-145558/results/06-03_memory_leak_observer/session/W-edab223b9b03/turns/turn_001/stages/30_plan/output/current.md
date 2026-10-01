IDENTIFY the memory leak caused by EventEmitter observers never being unsubscribed when DataProcessor instances are discarded
EXPLAIN why persistent listeners prevent garbage collection of DataProcessor objects
MODIFY the DataProcessor implementation to remove its listener after use, ensuring no lingering references
PROVIDE a test that demonstrates the leak exists before the fix by tracking object count or memory usage over many calls to process_batch
SHOW that the leak is resolved after applying the fix by the same tracking method
