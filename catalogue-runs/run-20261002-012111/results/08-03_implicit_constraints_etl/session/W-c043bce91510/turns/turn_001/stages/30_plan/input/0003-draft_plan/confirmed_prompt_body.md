IDENTIFY all implicit ordering dependencies in the ETL pipeline and produce a correct execution DAG.
DEFINE nodes for each pipeline step using the exact entity names:
    EXTRACT from sales database (PostgreSQL)
    EXTRACT from inventory CSV export
    EXTRACT from customer API (subject to 100 requests per minute)
    ENRICH sales records with customer names and addresses
    JOIN inventory levels with sales to compute stock‑out risk
    GENERATE daily summary that combines all three datasets
    LOAD the summary into the data warehouse
    PURGE stale data older than 90 days from the data warehouse after loading
ESTABLISH directed edges to reflect ordering constraints:
    EXTRACT from sales database (PostgreSQL) -> ENRICH
    EXTRACT from inventory CSV export -> JOIN
    EXTRACT from customer API (subject to 100 requests per minute) -> ENRICH
    ENRICH -> JOIN
    JOIN -> GENERATE
    GENERATE -> LOAD
    LOAD -> PURGE
ENSURE the purge step occurs only after loading.
ENSURE the extraction from customer API respects the rate limit of 100 requests per minute.
OUTPUT the DAG in a clear representation (e.g., list of nodes and edges).
