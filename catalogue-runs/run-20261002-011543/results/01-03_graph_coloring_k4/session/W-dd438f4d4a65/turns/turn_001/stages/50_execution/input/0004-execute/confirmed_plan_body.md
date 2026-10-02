DEFINE graph representation of wheel graph W_11
GENERATE adjacency list for hub node 0 and peripheral nodes 1-11
SELECT a generic 4-coloring algorithm suitable for wheel graphs
APPLY the algorithm to assign colors from {1,2,3,4} to each node
VERIFY that no two adjacent nodes share the same color
OUTPUT the assigned colors for nodes 0, 1, 2, 3, 4, 11

PROVE impossibility of a 3-coloring
    IDENTIFY the peripheral cycle as an odd-length cycle
    ARGUE that an odd cycle cannot be properly colored with only 2 colors, thus requires at least 3 colors
    NOTE that the hub node 0 is adjacent to every peripheral node
    DEDUCE that with only 3 colors, the hub cannot be assigned a distinct color from all its neighbors
    CONCLUDE that a proper coloring of W_11 requires at least 4 colors
