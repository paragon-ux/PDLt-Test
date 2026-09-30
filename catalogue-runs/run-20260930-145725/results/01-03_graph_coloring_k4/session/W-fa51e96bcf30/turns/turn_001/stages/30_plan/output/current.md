DEFINE the wheel graph W_11 with hub node 0 and peripheral nodes 1 through 11 forming a cycle
ASSIGN colors {1,2,3,4} to nodes ensuring adjacent nodes receive different colors
- COLOR hub node 0 with color 1
- COLOR peripheral nodes sequentially using colors 2,3,4,2,3,4,2,3,4,2,3 to satisfy adjacency constraints on the cycle and hub edges
VERIFY that all edges of W_11 connect nodes of different colors
DOCUMENT the resulting color assignment for each node as the valid 4‑coloring
PROVE that a 3‑coloring is impossible
- NOTE that the peripheral cycle of length 11 is odd and therefore requires at least three colors
- OBSERVE that the hub node is adjacent to every peripheral node, forcing the hub to use a color distinct from all colors used on the cycle
- CONCLUDE that the combination of an odd peripheral cycle and the hub node forces the use of a fourth color, making a 3‑coloring insufficient
PREPARE the proof outline referencing the node identifiers W_11, 0, 1‑11 as required
