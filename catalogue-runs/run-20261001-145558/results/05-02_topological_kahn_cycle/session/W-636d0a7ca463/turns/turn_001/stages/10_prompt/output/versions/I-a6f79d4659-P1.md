READ directed graph as adjacency list
APPLY Kahn's algorithm for topological sorting
IF cycle detected THEN REPORT the actual cycle sequence of nodes
ELSE RETURN a valid topological ordering
TEST with a valid DAG of 8 nodes ensuring ordering respects all edges
TEST with a graph containing a cycle verifying reported cycle is valid
