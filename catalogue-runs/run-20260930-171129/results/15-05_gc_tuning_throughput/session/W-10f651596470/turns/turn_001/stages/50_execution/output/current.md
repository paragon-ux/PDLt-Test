Generation‑2 (old‑generation) collections become slower when the number of objects promoted to that generation grows large. In the log the objects in generation 2 increase from 287 634 to 342 109 across three collections, and the elapsed time rises from 0.083 s to 0.146 s – a clear correlation.

**Why the slowdown**
* The collector scans every object in generation 2 to find unreachable ones. Its cost is roughly linear in the live object count, so more live objects ⇒ longer pause.
* When many objects survive long enough to be promoted, the old‑generation heap becomes large and fragmented, making the mark‑and‑sweep phase more expensive.
* Frequent promotion of short‑lived containers (lists, dicts, sets) and custom objects exacerbates the problem because each promotion adds to the live set.

**What the growing count indicates**
* The application is retaining a growing number of objects for a long time – either a true memory‑leak or a workload pattern that legitimately keeps many objects alive.
* The high steady‑state size of generation 2 suggests that the “young‑generation” thresholds are too low, causing premature promotion of objects that could have been collected earlier.

**Three common code patterns that cause this**
1. **Long‑lived container growth** – appending to a global list or dict inside a loop without purging old entries (e.g., accumulating log records, cache entries, or metric samples).
2. **Reference cycles involving user‑defined objects** – objects that reference each other (or themselves) and also hold large containers, preventing reference‑count deallocation and forcing the cyclic‑gc to handle them in generation 2.
3. **Frequent creation of large temporary containers** – building big lists/dicts inside tight loops where a portion of the data is inadvertently kept alive (e.g., storing slices of a large list for later processing).

**Tuning recommendations**
* **gc.set_threshold(threshold0, threshold1, threshold2)** – raise `threshold0` (young‑gen) to delay promotions, e.g., `gc.set_threshold(700, 10, 10)`. This reduces the rate at which objects reach generation 2.
* **gc.freeze()** – after the system reaches a steady‑state where the old‑generation set is stable, call `gc.freeze()` to stop generation‑2 collections entirely for the duration of the critical path (useful for latency‑sensitive sections).
* **gc.disable()** – for short‑lived, high‑throughput phases where you can tolerate some temporary memory growth, disable the collector and run an explicit `gc.collect()` at a convenient safe point.
* Combine the above: keep the collector enabled for the rest of the program, but before a latency‑critical operation, `gc.freeze()` (or `gc.disable()`), perform the work, then `gc.enable()` / `gc.collect()` afterwards.

In practice, start by profiling object lifetimes (e.g., using `objgraph` or `tracemalloc`) to confirm which pattern is present, then adjust thresholds or insert freeze/disable calls around the identified hot path.

---
Result IR:
{"files":[{"filename":"diagnosis.txt","satisfies":["R1","R2","R3","R4"],"evidence":{"path":"execution://body","section":null,"observed":"Generation‑2 (old‑generation) collections become slower when the number of objects promoted to that generation grows large."}}],"reconciliation":[{"requirement":"R1","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"Generation‑2 (old‑generation) collections become slower when the number of objects promoted to that generation grows large."}},{"requirement":"R2","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"the objects in generation 2 increase from 287 634 to 342 109 across three collections"}},{"requirement":"R3","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"Three common code patterns that cause this"}},{"requirement":"R4","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"tuning recommendations (gc.set_threshold, gc.freeze, or gc.disable)"}}],"open_defects":[]}
