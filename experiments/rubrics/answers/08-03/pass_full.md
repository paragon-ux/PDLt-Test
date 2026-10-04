**Implicit dependencies**
- extract_sales, extract_inventory, extract_customers have no inputs from each other: run in parallel.
- enrich_sales needs extract_sales + extract_customers (names and addresses).
- compute_stockout_risk needs extract_inventory + sales (it joins inventory with sales; using enriched sales is fine but not required).
- build_daily_summary needs enrich_sales + compute_stockout_risk + extract_customers ("combining all three datasets").
- load_warehouse needs build_daily_summary.
- purge_stale (> 90 days) needs load_warehouse; running it before the load would purge before the new day lands, or delete rows the load depends on.
- The customer API's 100 req/min limit bounds extract_customers: batch requests, throttle, cache unchanged customers, and schedule it first since it is the long pole.

**DAG**
```
extract_sales ─────┬──────────────► enrich_sales ─────────┐
extract_customers ─┴───────────────────────────────────────┤
extract_sales ─────┬──► compute_stockout_risk ─────────────┼─► build_daily_summary ─► load_warehouse ─► purge_stale
extract_inventory ─┘                                        │
extract_customers ──────────────────────────────────────────┘
```
