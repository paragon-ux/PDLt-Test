IDENTIFY implicit ordering dependencies in the described ETL pipeline and produce a correct execution DAG.
EXTRACT data from the sales database (PostgreSQL).
EXTRACT data from the inventory CSV export.
EXTRACT data from the customer API (rate‑limited to 100 requests per minute).
ENRICH sales records with customer names and addresses.
JOIN inventory levels with sales to compute stock‑out risk.
GENERATE a daily summary combining sales database, inventory CSV export, and customer API data.
LOAD the daily summary into the data warehouse.
PURGE stale data older than 90 days from the data warehouse.
OUTPUT the execution DAG representing the above steps and their ordering dependencies.
