**Little's Law.** A request holds a DB connection for the DB wait: 15 ms query + 5 ms round trip = 20 ms. L = λ × W = 2,000 req/s × 0.020 s = **40 connections busy on average**. Requests in flight overall: 2,000 × 0.050 s = 100, well under the 200 threads.

**Amdahl.** 40% of each request's time (20/50 ms) is DB-bound; only that fraction scales with pool size. The database itself has 16 cores; once active queries exceed roughly 2 × cores (~32), extra connections only queue inside the database, adding context switching and lock contention without throughput. So the useful pool is bounded below by ~40 (to sustain the load) and the database's capacity sets the ceiling.

**Too small** (say 20): only 20 × (1/0.020) = 1,000 req/s of DB work; the rest of the threads block on the pool, latency rises without bound, and requests time out.

**Too large** (say 200): during a spike the database runs 200 concurrent queries on 16 cores: context switches, memory per connection (~5-10 MB each in PostgreSQL), lock contention, and lower throughput than a smaller pool.

**Recommendation:** about 50 connections (40 average + ~25% headroom for variance and bursts), with a short acquisition timeout and pool metrics; revisit if query time changes, since the size scales with W.
