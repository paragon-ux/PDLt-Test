**Analysis of Load Test Results**

1. **Saturation Point**
   - Throughput increases rapidly up to 300 concurrent users (2,680 req/s) and then plateaus. From 300 to 500 users the throughput rises only slightly (2,680 → 2,710 req/s), and at 1000 users it actually drops to 2,650 req/s. Therefore, the saturation point is around **300 concurrent users** where throughput begins to level off.

2. **Primary Bottleneck Resource**
   - **CPU usage** reaches 98 % at 300 users and stays at 99 % for higher loads, indicating the CPU is fully utilized.
   - **Memory usage** is still below critical thresholds (52 % at 300 users, 65 % at 500, 78 % at 1000), so memory is not the limiting factor yet.
   - **Database connections** are capped at 150 from 300 users onward, but the DB usage does not show a spike in latency until the extreme load of 1000 users, where response times explode. The combination of near‑maxed CPU and stable DB connections suggests the **CPU is the primary bottleneck**, with secondary pressure from the database at very high concurrency.

3. **Why Throughput Decreases at 1000 Users**
   - At 1000 users, average response time surges to 4500 ms (P95 = 12 000 ms, P99 = timeout) and error rate jumps to 23.4 %.
   - The CPU is already saturated at 99 %, leaving virtually no headroom for additional processing. The extreme response times cause requests to stack up, increasing queuing delays and timeouts, which in turn reduce the effective throughput despite the same number of concurrent users.
   - The high error rate further reduces successful request processing, contributing to the observed decline in throughput.

4. **Maximum Recommended Concurrent Users**
   - To stay within acceptable performance limits (response times < 200 ms, error rate < 1 %, CPU < 85 %), the system should be limited to **approximately 200 concurrent users**. At this level, average response time is 78 ms, P95 is 145 ms, and CPU usage is 91 % (still high but manageable). A more conservative recommendation would be **150 concurrent users** to keep CPU usage under 85 % and provide a safety margin.

5. **Scaling Recommendations**
   - **Vertical Scaling**: Increase CPU capacity (e.g., add more cores or move to a higher‑performance instance) to relieve the CPU bottleneck.
   - **Horizontal Scaling**: Deploy additional application instances behind a load balancer to distribute load, effectively increasing aggregate CPU resources.
   - **Database Optimization**: Since DB connections plateau at 150, consider increasing the connection pool size or scaling the database tier (read replicas or stronger DB instance) to handle higher concurrency.
   - **Caching**: Introduce an in‑memory cache (e.g., Redis) for frequently accessed data to reduce CPU work per request.
   - **Async Processing**: Offload long‑running tasks to background workers to free up request‑handling threads.
   - **Resource Monitoring**: Implement fine‑grained monitoring and auto‑scaling policies that trigger additional instances when CPU usage exceeds 80 %.

These actions together will raise the system’s capacity beyond the current saturation point and improve resilience under heavier loads.
