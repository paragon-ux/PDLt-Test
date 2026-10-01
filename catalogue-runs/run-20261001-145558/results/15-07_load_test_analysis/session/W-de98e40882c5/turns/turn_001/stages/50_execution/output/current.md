**Analysis of Load Test Results**

1. **Saturation Point**
   - Throughput increases rapidly from 10 to 200 concurrent users, reaching 2,560 req/s.
   - From 300 to 500 users the throughput only rises marginally (2,680 req/s → 2,710 req/s) and then slightly decreases at 1,000 users (2,650 req/s).  The plateau is therefore observed around **300 – 500 concurrent users**, with a peak throughput of roughly **2,700 req/s**.

2. **Primary Bottleneck Resource**
   - CPU usage hits **98 %–99 %** at 200 users and stays at 99 % for higher loads.
   - Memory usage is still below critical levels (52 % at 300 users, 78 % at 1,000 users) but climbs steadily.
   - The number of DB connections remains capped at **150** across all loads, indicating the DB connection pool is already saturated.
   - The combination of **CPU saturation** and a **fixed DB‑connection limit** suggests the **CPU is the immediate bottleneck**, with the DB connection pool as a secondary constraint that will become dominant as the system scales further.

3. **Why Throughput Decreases at 1,000 Users**
   - Average response time skyrockets to **4.5 s** (P95 = 12 s, P99 = timeout), causing request queuing and time‑outs.
   - Error rate jumps to **23.4 %**, indicating many requests fail due to time‑outs or server overload.
   - CPU is already maxed out, so additional work cannot be processed, leading to increased latency and drop in successful throughput.

4. **Maximum Recommended Concurrent Users**
   - To stay below the saturation plateau and keep error rates negligible, the system should be limited to the point just before the plateau begins.  A safe operating ceiling is **≈ 300 concurrent users** (throughput ≈ 2,680 req/s, error rate ≈ 1 %).  Pushing to 500 users yields only a marginal gain while approaching the limits of CPU and DB connections.

5. **Scaling Recommendations**
   - **Horizontal scaling of the application tier**: add more stateless service instances behind a load balancer to share the CPU load.  This will raise the effective CPU capacity and move the saturation point to higher concurrency levels.
   - **Increase DB connection pool size**: raise the maximum DB connections (e.g., to 300) and ensure the database can handle the extra connections, or introduce a read‑replica layer to distribute the load.
   - **Introduce caching**: cache frequent read‑only queries at the application level (e.g., Redis or in‑memory) to reduce CPU and DB pressure.
   - **Optimize CPU‑intensive code**: profile the application to identify hot paths and refactor or offload heavy computation (e.g., move to async I/O, use compiled extensions).
   - **Monitor and auto‑scale**: set up telemetry on CPU, memory, and DB connection usage; trigger auto‑scaling policies when CPU approaches 80 %.
   - **Consider vertical scaling**: if horizontal scaling is not feasible, upgrade the host CPU (more cores) and increase available memory to provide headroom before hitting the plateau again.

These actions will raise the throughput ceiling, keep latency low, and maintain a low error rate as the number of concurrent users grows.
