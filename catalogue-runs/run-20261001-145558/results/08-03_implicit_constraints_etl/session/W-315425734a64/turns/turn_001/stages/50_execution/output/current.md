# Execution DAG for the ETL Pipeline

## Nodes (Tasks)
1. **Extract Sales DB** – Pull sales data from PostgreSQL.
2. **Extract Inventory CSV** – Read inventory export file.
3. **Extract Customer API** – Retrieve customer records (must respect rate limit of 100 req/min).
4. **Enrich Sales with Customer Data** – Join sales records with customer information.
5. **Join Inventory Levels** – Combine enriched sales with inventory levels to compute stock‑out risk.
6. **Generate Daily Summary** – Aggregate results from enrichment and inventory join into a single summary dataset.
7. **Load Summary to Warehouse** – Insert the daily summary into the data warehouse.
8. **Purge Stale Data** – Delete warehouse records older than 90 days.

## Directed Edges (Dependencies)
- **Extract Sales DB** → **Enrich Sales with Customer Data**
- **Extract Customer API** → **Enrich Sales with Customer Data** (extraction must finish before enrichment; API rate‑limit enforced during this step)
- **Extract Inventory CSV** → **Join Inventory Levels**
- **Enrich Sales with Customer Data** → **Join Inventory Levels**
- **Join Inventory Levels** → **Generate Daily Summary**
- **Enrich Sales with Customer Data** → **Generate Daily Summary**
- **Generate Daily Summary** → **Load Summary to Warehouse**
- **Load Summary to Warehouse** → **Purge Stale Data**

## Rate‑Limit Consideration
The **Extract Customer API** node must be throttled to ≤100 requests per minute. In practice, this is enforced within the enrichment task (node 4) by batching API calls or using a rate‑limiting utility, ensuring the downstream dependency respects the limit.

## DAG Visualisation (ASCII)
```
Extract Sales DB ----
                     |
Extract Customer API -+--> Enrich Sales with Customer Data ----
                                                   |            |
Extract Inventory CSV ----------------------------+            |
                                                        Join Inventory Levels
                                                               |
                                                   Generate Daily Summary
                                                               |
                                                   Load Summary to Warehouse
                                                               |
                                                     Purge Stale Data
```
