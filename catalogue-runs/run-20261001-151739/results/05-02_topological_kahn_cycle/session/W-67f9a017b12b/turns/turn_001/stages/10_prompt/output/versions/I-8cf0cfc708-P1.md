USE Python.
READ a directed graph represented as an adjacency list.
APPLY Kahn's algorithm for topological sorting with cycle detection.
IF a cycle exists THEN IDENTIFY the nodes that form the cycle and REPORT an error indicating which nodes form a cycle, providing the actual cycle (sequence of nodes).
ELSE RETURN a valid topological ordering.
TEST the implementation with:
- A valid DAG with 8 nodes, verify the ordering respects all edges.
- A graph with a cycle, verify the reported cycle is valid.
