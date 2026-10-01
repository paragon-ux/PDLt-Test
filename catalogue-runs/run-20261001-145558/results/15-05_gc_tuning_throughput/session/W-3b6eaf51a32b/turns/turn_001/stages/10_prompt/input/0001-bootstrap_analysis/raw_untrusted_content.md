Given the following GC log output from a Python application experiencing periodic latency spikes, diagnose the issue:

`
gc: collecting generation 2...
gc: objects in each generation: 892 4501 287634
gc: objects in permanent generation: 0
gc: done, 15234 unreachable, 0 uncollectable, 0.0834s elapsed
gc: collecting generation 2...
gc: objects in each generation: 711 5102 303892
gc: done, 18902 unreachable, 0 uncollectable, 0.1021s elapsed
gc: collecting generation 2...
gc: objects in each generation: 1203 4892 342109
gc: done, 23451 unreachable, 0 uncollectable, 0.1456s elapsed
`

Explain: (1) why generation 2 collections are getting slower, (2) what the growing object count in generation 2 indicates, (3) three specific code patterns that commonly cause this, and (4) tuning recommendations (gc.set_threshold, gc.freeze, or gc.disable for specific operations).
