CALCULATE the theoretical optimal connection pool size for the web application using the supplied measurements.
APPLY Little's Law (L = λ * W) with request rate 2000 requests/second and average total request time derived from the given components.
APPLY Amdahl's Law to account for the parallelizable portion of request processing and the limitation of database server CPU cores (16).
EXPLAIN the consequences of a pool size that is too small (queue buildup, increased latency) and too large (excess thread contention, resource exhaustion).
RECOMMEND a justified optimal connection pool size based on the calculations and explained trade‑offs.
INCLUDE the following operative task entities verbatim in the description: 50ms, 20ms, 15ms, 5ms, 200, 2000, 16, optimal connection pool size, Little's Law, Amdahl's Law.
