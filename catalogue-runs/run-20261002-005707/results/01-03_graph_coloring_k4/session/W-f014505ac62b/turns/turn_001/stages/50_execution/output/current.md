4-Coloring Assignment:
Node 0: 1
Node 1: 2
Node 2: 3
Node 3: 2
Node 4: 3
Node 5: 2
Node 6: 3
Node 7: 2
Node 8: 3
Node 9: 2
Node 10: 3
Node 11: 4

Proof that 3 colors are insufficient:
The wheel graph W₁₁ contains an odd cycle formed by the peripheral nodes 1‑2‑3‑…‑11‑1, which has length 11. An odd cycle requires at least 3 distinct colors in any proper coloring, because a 2‑coloring would force the start and end vertices of the cycle to share a color, violating the edge (11,1).
Assume, for contradiction, that a 3‑coloring exists for W₁₁. Let the three colors be A, B, and C. The odd cycle must use all three colors, and because it has an odd number of vertices, the color pattern around the cycle cannot alternate perfectly; at least one color must appear twice adjacent to the hub node 0. Since node 0 is adjacent to every peripheral node, it must be colored with a color different from each of the 11 peripheral colors. With only three colors available, node 0 would inevitably share a color with at least one peripheral node, creating a conflict. Hence a 3‑coloring is impossible, and at least 4 colors are required.
The provided assignment uses four colors and satisfies all adjacency constraints, proving the claim.
