READ the directed graph supplied as an adjacency list
EXECUTE Kahn's algorithm to produce a topological ordering of the nodes
IF a cycle is detected THEN OUTPUT an error that includes the nodes forming the cycle
PROVIDE a test case with a valid DAG of eight nodes and verify that the returned ordering respects all edges
PROVIDE a test case with a graph that contains a cycle and verify that the reported cycle is correct
