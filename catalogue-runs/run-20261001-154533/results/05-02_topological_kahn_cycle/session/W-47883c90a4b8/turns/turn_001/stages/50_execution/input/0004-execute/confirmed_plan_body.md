RECEIVE the directed graph as an adjacency list.
VALIDATE that the input conforms to the adjacency‑list format.
COMPUTE indegree for each node.
INITIALIZE a collection (queue) of nodes whose indegree is zero.
WHILE the collection is not empty:
    REMOVE a node from the collection.
    APPEND the node to the topological ordering.
    FOR each neighbor reachable from the removed node:
        DECREMENT the neighbor's indegree.
        IF the neighbor's indegree becomes zero THEN ADD the neighbor to the collection.
IF the topological ordering includes all nodes THEN RETURN the ordering.
ELSE IDENTIFY the remaining nodes that form cycles.
    DETECT a cycle among the remaining nodes and EXTRACT the cycle sequence.
    RETURN an error containing the detected cycle nodes in order.
GENERATE a test case representing a valid DAG with eight nodes and diverse edges.
EXECUTE the algorithm on the DAG test case and VERIFY that the output ordering respects every edge.
GENERATE a test case representing a graph that contains a cycle.
EXECUTE the algorithm on the cycle test case and VERIFY that the error output includes a valid cycle sequence.
PACKAGE the Python implementation, the cycle‑detection extension, and the two test cases as the final deliverable.
