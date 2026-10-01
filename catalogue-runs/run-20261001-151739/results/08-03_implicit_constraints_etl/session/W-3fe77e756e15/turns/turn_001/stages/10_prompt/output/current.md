IDENTIFY all implicit ordering dependencies in the ETL pipeline
EXTRACT data from sales database (PostgreSQL)
EXTRACT data from inventory CSV export
EXTRACT data from customer API subject to 100 requests per minute
ENRICH sales records with customer names and addresses
JOIN inventory levels with sales to compute stock‑out risk
GENERATE a daily summary by combining the three datasets
LOAD the daily summary into the data warehouse
PURGE stale data older than 90 days from the data warehouse after loading
OUTPUT a DAG representing the required execution order that respects the identified dependencies
