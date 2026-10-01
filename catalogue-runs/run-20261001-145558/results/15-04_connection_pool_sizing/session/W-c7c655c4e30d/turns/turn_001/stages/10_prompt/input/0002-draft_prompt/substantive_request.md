TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Derive the optimal connection pool size for a web application using the provided measurements: average request processing time 50ms (20ms waiting for database), database query execution time 15ms average, network round-trip to database 5ms, application server threads 200, request rate 2000 requests/second, database server CPU cores 16. Apply Little's Law (L = λ * W) and Amdahl's Law to compute: 1) theoretical optimal pool size, 2) effects of a pool that is too small (thread starvation), 3) effects of a pool that is too large (connection overhead, database contention), and 4) recommend a pool size with justification.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- average request processing time 50ms
- database query execution time 15ms
- application server threads 200
- request rate 2000 requests/second
- database server CPU cores 16
- Little's Law
- Amdahl's Law
- connection pool size
