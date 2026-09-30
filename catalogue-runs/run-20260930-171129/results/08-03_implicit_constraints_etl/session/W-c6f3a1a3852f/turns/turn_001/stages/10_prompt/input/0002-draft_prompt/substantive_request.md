TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify implicit ordering dependencies in the described ETL pipeline and produce a correct execution DAG. The pipeline extracts data from three sources: the sales database (PostgreSQL), the inventory CSV export, and the customer API (rate‑limited to 100 requests per minute). Sales records are enriched with customer names and addresses. Inventory levels are joined with sales to compute stock‑out risk. A daily summary combining all three datasets is generated and loaded into the data warehouse. After loading, stale data older than 90 days is purged from the warehouse.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- sales database
- PostgreSQL
- inventory CSV export
- customer API
- daily summary
- data warehouse
- purge
- 90 days
