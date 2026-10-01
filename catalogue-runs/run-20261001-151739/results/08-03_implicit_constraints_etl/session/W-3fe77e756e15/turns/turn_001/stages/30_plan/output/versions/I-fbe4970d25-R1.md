IDENTIFY implicit ordering dependencies in the ETL pipeline
EXTRACT data from the sales PostgreSQL database
EXTRACT data from the inventory CSV export
EXTRACT data from the customer API subject to a limit of 100 requests per minute
ENRICH sales records with customer names and addresses
JOIN inventory levels with sales records to compute stock-out risk
GENERATE a daily summary by combining the three datasets
LOAD the daily summary into the data warehouse
PURGE stale data older than 90 days from the data warehouse after loading
BUILD a DAG that represents the required execution order respecting the identified dependencies
OUTPUT the DAG
