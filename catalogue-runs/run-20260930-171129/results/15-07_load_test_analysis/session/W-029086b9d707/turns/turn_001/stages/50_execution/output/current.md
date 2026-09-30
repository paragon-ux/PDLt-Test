**Interpretation of Load Test Results**

1. **Saturation Point**
   - Throughput increases with concurrent users up to about 500 users (2,710 req/s) and then plateaus. The plateau begins around 300‑500 users, where additional users no longer raise throughput appreciably.

2. **Primary Bottleneck Resource**
   - CPU utilization hits 99 % at 200 users and stays at 99 % beyond that. Memory usage and DB connections are still below their limits, but CPU is saturated. Therefore the CPU is the primary bottleneck.

3. **Why Throughput Decreases at 1,000 Users**
   - At 1,000 users the CPU remains at 99 % but the system experiences severe response‑time degradation (average 4.5 s, P95 12 s, P99 timeout) and a high error rate (23.4 %). The kernel is spending most of its time scheduling, leading to queuing delays and request timeouts, which cause the observed drop in throughput.

4. **Maximum Recommended Concurrent Users**
   - To stay below the CPU saturation threshold and keep error rate under 1 %, the safe operating point is around **300 – 350 concurrent users**. At 300 users the error rate is 1.2 % and CPU is 98 %; at 200 users the error rate is 0.1 % and CPU is 91 %.

5. **Scaling Recommendations**
   - **Vertical Scaling**: Increase the number of CPU cores or move to higher‑performance instances to raise the CPU ceiling.
   - **Horizontal Scaling**: Deploy additional application replicas behind a load balancer and ensure the database can handle increased connections (currently capped at 150). Use connection pooling and consider read‑replicas.
   - **Optimization**: Profile hot code paths, optimize CPU‑intensive algorithms, and enable caching to reduce per‑request CPU work.
   - **Resource Limits**: Set alerts for CPU > 90 % and error‑rate > 2 % to trigger auto‑scaling before the system reaches the saturation plateau.

These actions will move the saturation point to higher concurrency levels and improve overall system stability.
