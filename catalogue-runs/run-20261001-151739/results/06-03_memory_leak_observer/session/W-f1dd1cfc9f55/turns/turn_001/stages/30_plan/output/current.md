ANALYZE the EventEmitter/DataProcessor implementation to locate listeners added via the on method for the data event.
DETERMINE the reference graph that retains DataProcessor instances after process_batch completes.
DESCRIBE why the listeners keep DataProcessor instances alive.
DESIGN a modification that unsubscribes the DataProcessor's listener after processing completes or uses weak references, preserving the literal identifiers EventEmitter, DataProcessor, process_batch, on, and data.
IMPLEMENT the designed modification in the code.
DEVELOP a test that repeatedly calls process_batch on the original code and measures the number of live DataProcessor objects to demonstrate the memory leak.
EXECUTE the pre‑fix test and RECORD the increase in object count.
DEVELOP a comparable test that runs after the modification and measures the number of live DataProcessor objects.
EXECUTE the post‑fix test and VERIFY that the object count does not increase, demonstrating leak resolution.
