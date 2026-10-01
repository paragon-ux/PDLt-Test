TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify implicit ordering dependencies in the described ETL pipeline and produce a correct execution DAG. The pipeline extracts data from three sources (sales database (PostgreSQL), inventory CSV export, and customer API), enriches sales records with customer information, joins inventory levels with sales to compute stock-out risk, generates a daily summary combining all three datasets, loads the summary into the data warehouse, and then purges stale data older than 90 days from the warehouse. The customer API has a rate limit of 100 requests per minute.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- sales database (PostgreSQL)
- inventory CSV export
- customer API
- daily summary
- data warehouse
