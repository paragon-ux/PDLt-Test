PARSE input adjacency list into graph data structure
EXECUTE Kahn's algorithm to compute topological order while detecting cycles
IF a cycle is detected THEN
    IDENTIFY nodes constituting the cycle
    REPORT error with the identified cycle sequence
ELSE
    RETURN computed topological ordering
TEST implementation with a valid DAG of eight nodes, VERIFY that the ordering respects all edges
TEST implementation with a graph containing a cycle, VERIFY that the reported cycle is accurate
