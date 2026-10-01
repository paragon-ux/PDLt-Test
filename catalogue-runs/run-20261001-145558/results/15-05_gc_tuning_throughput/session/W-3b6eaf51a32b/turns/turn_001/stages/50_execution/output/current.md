**Analysis:**

The GC log shows three successive generation‑2 collections with increasing latency (0.0834 s, 0.1021 s, 0.1456 s) and a rising number of objects in generation 2 (287 634 → 303 892 → 342 109). Generation‑2 collections become slower because:
1. **More long‑lived objects** – each collection must scan and possibly move a larger set of objects, increasing pause time.
2. **Growing reachability graph** – as more objects survive multiple collections, the root set and inter‑object references become denser, making the mark‑phase more expensive.
3. **Potential fragmentation** – many allocations and de‑allocations can fragment memory, causing the collector to spend extra time consolidating.

The rising generation‑2 object count indicates that the application is retaining a growing pool of long‑lived objects. This typically means that objects are not becoming unreachable after the usual two‑generation promotion cycle, often due to lingering references.

**Three common code patterns that cause this behavior:**
1. **Persistent reference cycles** – objects that reference each other (directly or indirectly) and are stored in global or long‑lived containers, preventing garbage collection.
2. **Global caches or singletons** – dictionaries, lists, or custom caches that accumulate entries over time without eviction, e.g., `functools.lru_cache(maxsize=None)` or module‑level dicts used as caches.
3. **Large container structures** – data structures such as big lists, dicts, or NumPy arrays that hold many objects and are kept alive for the lifetime of the program, e.g., a growing list of request objects or a tree of nodes retained by a manager.

**Tuning recommendations:**
- **`gc.set_threshold`** – Increase the thresholds for generation 0 and 1 to reduce the frequency of full collections if the workload consists mainly of short‑lived objects and the overhead of frequent collections is problematic. Example: `gc.set_threshold(700, 10, 10)`. For operations that temporarily allocate many objects, raise the thresholds before the operation and restore them afterwards.
- **`gc.freeze`** – Use `gc.freeze()` during latency‑sensitive sections where the program holds many long‑lived objects but performs little allocation (e.g., read‑only processing). This disables automatic GC temporarily, avoiding pause spikes. Remember to call `gc.unfreeze()` afterwards.
- **`gc.disable`** – For tightly scoped, high‑throughput loops that allocate many short‑lived objects and where you can manually manage memory, disable the collector with `gc.disable()` before the loop and re‑enable it with `gc.enable()` afterward, optionally invoking `gc.collect()` manually at a convenient point.

By applying these recommendations to the identified patterns—e.g., clearing global caches after use, breaking reference cycles, or disabling GC around intensive short‑lived workloads—you can mitigate the growing generation‑2 latency and keep the long‑lived object count in check.
