Implement Kahn's algorithm for topological sorting in Python with cycle detection:
1. Input: a directed graph as an adjacency list.
2. Output: a valid topological ordering, or an error indicating which nodes form a cycle.
3. When a cycle is detected, report the actual cycle (sequence of nodes), not just "cycle exists."
4. Test with: (a) a valid DAG with 8 nodes, verify ordering respects all edges; (b) a graph with a cycle, verify the reported cycle is valid.
