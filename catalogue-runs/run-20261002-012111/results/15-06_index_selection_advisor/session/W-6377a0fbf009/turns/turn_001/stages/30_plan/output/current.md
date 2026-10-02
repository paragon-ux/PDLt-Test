PARSE the query workload definitions for the events table
EXTRACT filter, order, group, and JSONB containment predicates from each query
IDENTIFY unique column combinations used in predicates
FOR each unique column combination
    DETERMINE suitable index type (e.g., BTREE for scalar columns, GIN for JSONB)
    FORMULATE a candidate CREATE INDEX definition for the column combination and index type
    ESTIMATE the storage overhead for the candidate index
    ASSIGN the candidate index to the queries that can benefit from it
ENDFOR
COMPOSE the CREATE INDEX statements with explanations of which queries each index serves
OUTPUT the composed index recommendations
