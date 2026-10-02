PARSE the supplied Python observer pattern implementation
INSPECT the EventEmitter class for observer registration mechanics
DETECT any persistent references to bound methods such as DataProcessor.handle_data
EVALUATE the reference graph to determine impact on DataProcessor garbage collection
CONSTRUCT a high-level explanation of the memory leak cause
DESIGN a lifecycle management approach, e.g., an unsubscribe method or destructor cleanup
IMPLEMENT an unsubscribe method in EventEmitter (or modify DataProcessor destructor) as a high-level operation
MODIFY the usage of EventEmitter to deregister callbacks when DataProcessor is no longer needed
PREPARE a test harness that creates a DataProcessor instance, registers observers, and monitors object lifetime using weakref or object counting
EXECUTE the test before applying the fix to demonstrate the leak
APPLY the lifecycle fix modifications to the code
RE-EXECUTE the test after the fix to verify leak resolution
LIST verbatim the operative task entities: EventEmitter, on, DataProcessor, handle_data, process_batch, batch, 'data'
