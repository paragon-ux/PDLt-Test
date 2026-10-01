INTERPRET wheel graph definition
BUILD internal representation of nodes 0-11 with edges (0-1 through 0-11) and outer-cycle edges (1-2, 2-3, ..., 11-1)
APPLY a 4-coloring algorithm using colors {1,2,3,4} to assign a color to each node while respecting adjacency constraints
VERIFY that no adjacent nodes share the same color
EMIT the 4-coloring assignment
ATTEMPT a 3-coloring algorithm using colors {1,2,3}
IF a valid 3-coloring is found
    EMIT the 3-coloring assignment
ELSE
    CONSTRUCT a proof outline demonstrating that a 3-coloring cannot satisfy all adjacency constraints for this wheel graph
    EMIT the proof statement that 3 colors are insufficient
