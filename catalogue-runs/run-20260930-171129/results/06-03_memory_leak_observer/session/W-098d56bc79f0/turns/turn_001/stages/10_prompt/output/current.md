IDENTIFY the memory leak caused by the EventEmitter observer pattern where DataProcessor instances are never unsubscribed.
EXPLAIN why the leak prevents garbage collection of DataProcessor objects.
MODIFY the code so that each DataProcessor unregisters its listener after processing, managing the lifecycle of observers.
PROVIDE a test that demonstrates the leak exists when process_batch is called many times and shows that memory usage stabilizes after applying the fix.
INCLUDE the operative task entities exactly as listed: EventEmitter, on, DataProcessor, process_batch, batch.
