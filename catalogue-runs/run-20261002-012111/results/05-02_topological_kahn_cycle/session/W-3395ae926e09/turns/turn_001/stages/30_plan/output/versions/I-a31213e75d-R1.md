LIST the operative task entities: Kahn's algorithm; topological sorting; Python; directed graph; adjacency list; cycle detection.
READ the directed graph provided as an adjacency list in Python.
APPLY Kahn's algorithm to compute a topological ordering.
IF a cycle is detected THEN
    REPORT the sequence of nodes that form the cycle.
ELSE
    RETURN a valid topological ordering that respects all edges.
VERIFY the solution with two test cases:
    (a) a directed acyclic graph with 8 nodes, check that the ordering respects all edges.
    (b) a graph containing a cycle, check that the reported cycle is correct.
OUTPUT the result as either the topological ordering or the cycle report.
