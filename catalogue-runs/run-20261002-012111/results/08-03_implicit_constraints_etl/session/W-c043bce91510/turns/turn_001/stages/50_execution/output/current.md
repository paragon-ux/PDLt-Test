Nodes:
- EXTRACT from sales database (PostgreSQL)
- EXTRACT from inventory CSV export
- EXTRACT from customer API (subject to 100 requests per minute)
- ENRICH sales records with customer names and addresses
- JOIN inventory levels with sales to compute stock‑out risk
- GENERATE daily summary that combines all three datasets
- LOAD the summary into the data warehouse
- PURGE stale data older than 90 days from the data warehouse after loading

Edges:
- EXTRACT from sales database (PostgreSQL) -> ENRICH sales records with customer names and addresses
- EXTRACT from inventory CSV export -> JOIN inventory levels with sales to compute stock‑out risk
- EXTRACT from customer API (subject to 100 requests per minute) -> ENRICH sales records with customer names and addresses
- ENRICH sales records with customer names and addresses -> JOIN inventory levels with sales to compute stock‑out risk
- JOIN inventory levels with sales to compute stock‑out risk -> GENERATE daily summary that combines all three datasets
- GENERATE daily summary that combines all three datasets -> LOAD the summary into the data warehouse
- LOAD the summary into the data warehouse -> PURGE stale data older than 90 days from the data warehouse after loading

Rate limit note: Extraction from the customer API must be scheduled respecting 100 requests per minute before the ENRICH step.
