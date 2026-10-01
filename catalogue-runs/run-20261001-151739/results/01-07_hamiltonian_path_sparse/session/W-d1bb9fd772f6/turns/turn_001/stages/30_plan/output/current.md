DEFINE BACKTRACK:
    INITIALIZE an empty path candidate
    SELECT a start node from G
    PERFORM a backtracking search with pruning to explore node orderings
    IF a Hamiltonian path is found THEN
        OUTPUT the complete path
        VERIFY that the path includes all 12 nodes
        VERIFY that each consecutive pair of nodes in the path corresponds to an edge in G
    ELSE
        OUTPUT that no Hamiltonian path exists
