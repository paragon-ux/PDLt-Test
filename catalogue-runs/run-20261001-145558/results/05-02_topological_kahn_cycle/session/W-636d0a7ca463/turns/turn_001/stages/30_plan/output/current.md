READ directed graph as adjacency list
APPLY Kahn's algorithm for topological sorting
IF a cycle is detected THEN REPORT the actual cycle sequence of nodes
ELSE RETURN a valid topological ordering
TEST the procedure with a valid DAG of eight nodes ensuring ordering respects all edges
TEST the procedure with a graph containing a cycle verifying the reported cycle is valid
