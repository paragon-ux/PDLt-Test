DEFINE the wheel graph W_11 with hub node 0 and peripheral nodes 1‑11 forming an odd cycle
SELECT a color assignment for node 0 from {1,2,3,4}
ASSIGN colors to peripheral nodes 1‑11 such that adjacent peripheral nodes receive different colors and no peripheral node shares the hub's color
VERIFY that each edge (0,i) and each edge (i,i+1 mod 11) connects nodes of distinct colors
OUTPUT the resulting 4‑coloring as the deliverable
ARGUE that any proper coloring of the odd peripheral cycle requires at least three distinct colors
SHOW that the hub node is adjacent to every peripheral node, forcing the hub's color to differ from all three colors used on the cycle
CONCLUDE that a proper coloring cannot be achieved with only three colors, establishing the necessity of a fourth color
