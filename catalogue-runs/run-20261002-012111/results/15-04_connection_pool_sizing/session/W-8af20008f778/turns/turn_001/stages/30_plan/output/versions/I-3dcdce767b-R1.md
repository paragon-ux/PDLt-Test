PARSE the supplied measurements
CALCULATE total request latency as the sum of average request processing time, database waiting time, database query execution time, and network round‑trip time
COMPUTE arrival rate λ from the given request rate
APPLY Little's Law to compute required concurrency L = λ * (total request latency)
ESTIMATE the parallelizable fraction of the workload based on the measured components
APPLY Amdahl's Law to compute the theoretical maximum concurrency improvement given the parallelizable fraction and the number of database server CPU cores
DERIVE the theoretical optimal connection pool size as the lesser of the concurrency required by Little's Law and the concurrency limit implied by Amdahl's Law and the database server capacity
DESCRIBE the consequences of a pool that is too small, emphasizing thread starvation and increased request latency
DESCRIBE the consequences of a pool that is too large, emphasizing connection overhead, increased contention on the database, and potential resource exhaustion
RECOMMEND a pool size based on the derived optimal size and justify the recommendation with reference to the calculations above
