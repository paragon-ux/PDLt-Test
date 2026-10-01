READ the wheel graph W_11 definition with hub node 0 and cycle nodes 1‑11
DEFINE the color set {1,2,3,4}
ASSIGN a color from the set to each node such that no two adjacent nodes share the same color
VERIFY adjacency constraints for all edges (0‑i for i=1..11 and i‑(i+1) modulo 11)
OUTPUT the resulting valid 4‑color assignment for all nodes
CONSTRUCT a logical argument that the 11‑node cycle is odd and therefore requires at least three distinct colors
NOTE that the hub node 0 is adjacent to every cycle node, so it cannot reuse any of the three colors used on the cycle
DEDUCE that a fourth color is necessary for the hub node
OUTPUT a proof statement asserting that no 3‑coloring exists for W_11
