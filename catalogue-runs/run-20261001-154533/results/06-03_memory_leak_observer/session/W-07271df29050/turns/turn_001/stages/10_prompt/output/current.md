IDENTIFY the memory leak in the Python observer pattern implementation where EventEmitter retains references to DataProcessor instances via the on('data', ...) subscription, preventing garbage collection when process_batch is invoked thousands of times.

EXPLAIN why the lingering listener (registered via on) stops the DataProcessor objects from being collected.

PROVIDE a corrected implementation that unsubscribes the DataProcessor's handle_data callback after each batch processing, for example by removing the listener or using a context manager.

INCLUDE a test that demonstrates the leak before the fix using weakref (showing DataProcessor instances remain alive after process_batch) and verifies that the leak is resolved after applying the fix.
