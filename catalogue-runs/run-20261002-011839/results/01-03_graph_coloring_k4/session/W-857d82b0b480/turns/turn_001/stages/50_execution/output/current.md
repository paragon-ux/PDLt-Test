4-Coloring assignment for the wheel graph W_11 (nodes 0‑11):

- Node 0 (hub): Color 4
- Nodes on the outer odd cycle (1‑11): use colors 1, 2, 3 alternating, but because the cycle length is 11 (odd) the alternation forces a conflict; we resolve it by assigning:
  * Node 1: Color 1
  * Node 2: Color 2
  * Node 3: Color 3
  * Node 4: Color 1
  * Node 5: Color 2
  * Node 6: Color 3
  * Node 7: Color 1
  * Node 8: Color 2
  * Node 9: Color 3
  * Node10: Color 1
  * Node11: Color 2

This assignment satisfies:
- Every edge (0,i) connects hub color 4 to a different color (1‑3), so no conflict.
- Every edge (i,i+1) on the outer cycle connects nodes of different colors because the pattern repeats every three nodes, and the cycle length 11 forces a mismatch only at the wrap‑around edge (11,1), which here connects colors 2 and 1 – also different.

Thus all adjacent nodes have distinct colors, providing a valid 4‑coloring.

Why a 3‑coloring is impossible:
The outer nodes 1‑11 form an odd cycle of length 11. An odd cycle requires at least 3 colors to avoid adjacent equal colors. The hub node 0 is adjacent to every outer node, so it must receive a color distinct from each of its neighbors. With only three colors available, the hub would have to reuse one of the three colors already used on the outer cycle, inevitably matching the color of at least one outer neighbor. Hence a fourth color is necessary to color the hub while keeping all adjacent nodes differently colored.

Therefore the wheel graph W_11 is not 3‑colorable, and the above assignment is a correct 4‑coloring.
