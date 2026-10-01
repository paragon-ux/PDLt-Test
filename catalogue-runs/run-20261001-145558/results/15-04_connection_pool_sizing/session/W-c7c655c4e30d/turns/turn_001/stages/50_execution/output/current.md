**Calculations**

1. **Little's Law** (L = λ * W)
   - Request rate (λ) = 2000 requests/second
   - Average request processing time (W) = 50 ms = 0.050 s
   - Required concurrent requests (L) = 2000 × 0.050 = **100 concurrent requests**
   - This is the average number of requests that must be in‑flight to sustain the given arrival rate.

2. **Amdahl’s Law** for the DB‑bound portion:
   - DB wait time per request = 20 ms (out of 50 ms total) → fraction *f* = 20 ms / 50 ms = **0.40**
   - Non‑DB (compute) fraction = 1 – f = **0.60**
   - Ideal speed‑up if we could parallelise the DB wait perfectly: 1 / ( (1‑f) + f / P )
   - Solving for *P* (effective parallel DB resources) that yields a realistic speed‑up gives a theoretical optimum where the pool size roughly matches the DB‑bound concurrency needed: **P ≈ L × f = 100 × 0.40 = 40**.
   - In practice the database server has 16 CPU cores; allowing ~2‑3 connections per core is typical, giving a practical upper bound of **≈ 32‑48** connections.

**Analysis of pool size extremes**

- *Too Small* (e.g., < 30 connections):
  - Requests that need a DB connection will block, causing thread starvation on the application server.
  - Latency spikes because queued requests wait for a free connection, often exceeding the 50 ms target.
  - Throughput drops as the server cannot keep up with the 2000 rps arrival rate.

- *Too Large* (e.g., > 80 connections):
  - Each extra connection consumes memory and maintains its own TCP socket, increasing overhead on both the app server and the DB server.
  - The DB may become a bottleneck: too many concurrent queries lead to contention for CPU, locks, and cache, reducing overall query performance.
  - Diminishing returns – beyond the point where the DB cores are saturated, additional connections only add latency.

**Recommendation**

Based on Little’s Law the system must handle about **100 concurrent requests**. Considering that only 40 % of a request’s time is spent waiting for the database, the effective DB‑bound concurrency needed is about **40 connections**. Aligning this with the database’s 16 cores and allowing roughly 2–3 connections per core yields a safe, performant range of **30‑45 connections**.

A pragmatic choice is to set the connection pool size to **40**. This value:
- Matches the DB‑bound concurrency derived from Little’s Law and Amdahl’s Law.
- Keeps the number of active connections well within the DB server’s CPU capacity (≈ 2.5 connections per core).
- Provides enough room for occasional spikes without causing thread starvation, while avoiding excessive overhead and contention.

If workload characteristics change (e.g., higher DB latency or more CPU‑intensive queries), revisit the pool size using the same calculations.
