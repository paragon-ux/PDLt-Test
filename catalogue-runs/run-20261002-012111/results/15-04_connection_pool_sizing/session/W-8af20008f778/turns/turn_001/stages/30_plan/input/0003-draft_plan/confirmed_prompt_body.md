DERIVE the optimal connection pool size for the web application based on the given measurements.
USE the following measurements:
    SET average request processing time = 50ms
    SET database waiting time = 20ms
    SET database query execution time = 15ms
    SET network round‑trip time to the database = 5ms
    SET application server threads = 200
    SET request rate = 2000 requests per second
    SET database server CPU cores = 16
APPLY Little's Law (L = λ * W) and Amdahl's Law to compute the theoretical optimal pool size.
DESCRIBE the consequences of a pool that is too small, focusing on thread starvation.
DESCRIBE the consequences of a pool that is too large, focusing on connection overhead and database contention.
RECOMMEND recommended pool size with justification.
