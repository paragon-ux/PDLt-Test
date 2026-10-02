TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify all implicit ordering dependencies in the described ETL pipeline and produce a correct execution DAG. The pipeline consists of extracting data from the sales database (PostgreSQL), extracting the inventory CSV export, extracting from the customer API (subject to a rate limit of 100 requests per minute), enriching sales records with customer names and addresses, joining inventory levels with sales to compute stock‑out risk, generating a daily summary that combines all three datasets, loading the summary into the data warehouse, and finally purging stale data older than 90 days from the warehouse after loading.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- sales database (PostgreSQL)
- inventory CSV export
- customer API
- daily summary
- data warehouse
- 100 requests per minute
- 90 days
