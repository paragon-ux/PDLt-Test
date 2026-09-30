IDENTIFY the memory leak caused by EventEmitter observers where DataProcessor instances remain subscribed
EXPLAIN why the persistent subscription prevents garbage collection of DataProcessor objects
MODIFY DataProcessor to unregister its listener after processing completes, ensuring observer lifecycle management
WRITE a test that repeatedly invokes process_batch to demonstrate unbounded memory growth before the fix
RUN the same test after applying the fix to show memory usage stabilizes
