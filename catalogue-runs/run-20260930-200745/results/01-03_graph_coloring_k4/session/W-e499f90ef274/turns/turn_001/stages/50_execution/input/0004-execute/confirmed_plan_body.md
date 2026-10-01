DEFINE the wheel graph W_11 with hub node 0 connected to peripheral nodes 1‑11 and peripheral nodes forming the odd cycle 1‑2‑…‑11‑1
SELECT a color from {1,2,3,4} for hub node 0
ASSIGN alternating colors from {1,2,3} to the peripheral cycle nodes ensuring that adjacent cycle nodes receive different colors
IF a conflict arises with the hub adjacency, ADJUST the color of one peripheral node to the fourth color
VERIFY that no two adjacent nodes share the same color across all edges
OUTPUT the resulting 4‑color assignment for all 12 nodes
ARGUE that the peripheral odd cycle alone requires at least 3 colors
NOTE that the hub node is adjacent to every peripheral node, forcing a color distinct from all three colors used on the cycle
CONCLUDE that 3 colors are insufficient and a 4‑coloring is necessary
