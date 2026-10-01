IDENTIFY implicit ordering dependencies in the described ETL pipeline and PRODUCE a correct execution DAG that respects those dependencies.
INCLUDE the following constraints:
- THE pipeline extracts data from three sources: sales database (PostgreSQL), inventory CSV export, and customer API.
- THE customer API rate limit is 100 requests per minute.
- ENRICH sales records with customer information.
- JOIN inventory levels with sales to compute stock-out risk.
- GENERATE a daily summary combining all three datasets.
- LOAD the summary into the data warehouse.
- PURGE stale data older than 90 days from the warehouse.
ENSURE the DAG orders these steps so that extraction precedes enrichment, enrichment and inventory join precede summary generation, summary loading precedes purge, and the API rate limit is respected during enrichment.
