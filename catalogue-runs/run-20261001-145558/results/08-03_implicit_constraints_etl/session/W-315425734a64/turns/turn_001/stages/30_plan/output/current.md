IDENTIFY extraction tasks for sales database, inventory CSV, and customer API
DETERMINE enrichment task that merges sales records with customer data
CALCULATE inventory join task that combines enriched sales with inventory levels to assess stock‑out risk
DEFINE summary generation task that aggregates results from enrichment and inventory join
SPECIFY load task that writes the daily summary into the data warehouse
DEFINE purge task that removes warehouse data older than 90 days
CONSTRUCT dependency graph ordering: extraction precedes enrichment; enrichment and inventory join precede summary generation; summary loading precedes purge
INCLUDE constraint that customer API extraction respects a maximum of 100 requests per minute during enrichment
