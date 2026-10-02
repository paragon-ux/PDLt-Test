IDENTIFY implicit ordering dependencies in the ETL pipeline
DEFINE nodes for each pipeline step using the exact entity names
ESTABLISH directed edges to reflect ordering constraints
ENSURE the purge step occurs only after loading
ENSURE the extraction from the customer API respects the rate limit of 100 requests per minute
COMPOSE the DAG representation as a list of nodes and edges
EMIT the DAG representation
