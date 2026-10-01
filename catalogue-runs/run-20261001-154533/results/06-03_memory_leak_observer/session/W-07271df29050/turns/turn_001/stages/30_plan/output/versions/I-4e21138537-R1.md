ANALYZE the supplied Python observer pattern implementation
IDENTIFY the reference chain that keeps DataProcessor instances alive via the EventEmitter on subscription
EXPLAIN why the lingering listener prevents DataProcessor objects from being garbage‑collected
DESIGN a corrected implementation that unsubscribes the DataProcessor's handle_data callback after each batch, e.g., by removing the listener or employing a context manager
IMPLEMENT the unsubscribing mechanism in the codebase
DEVELOP a test harness that creates a DataProcessor instance, stores a weakref to it, and invokes process_batch many times
RUN the test without the fix and VERIFY that the weakref remains non‑None after explicit garbage collection, indicating a leak
APPLY the corrected implementation
RUN the test with the fix and VERIFY that the weakref becomes None after garbage collection, confirming the leak is resolved
DOCUMENT the before‑and‑after observations
