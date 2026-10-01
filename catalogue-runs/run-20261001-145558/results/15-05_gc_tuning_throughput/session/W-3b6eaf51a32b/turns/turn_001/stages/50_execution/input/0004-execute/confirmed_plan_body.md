READ the Python GC log for generation 2 events
PARSE the log to extract timestamps, collection durations, and generation 2 object counts
AGGREGATE the collection durations to detect increasing latency trends
EVALUATE the relationship between growing generation 2 object counts and observed slowdown
IDENTIFY three code patterns that commonly increase long‑lived objects, such as persistent reference cycles, global caches retaining objects, and large container structures that hold many objects
FORMULATE tuning recommendations involving gc.set_threshold, gc.freeze, and gc.disable that address the identified patterns and operation contexts
