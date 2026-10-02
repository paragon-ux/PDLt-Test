**4‑coloring for W₁₁**

Let the color palette be {1,2,3,4}.  Assign colors as follows (node → color):

- 0 → 4  (hub)
- 1 → 1
- 2 → 2
- 3 → 1
- 4 → 2
- 5 → 1
- 6 → 2
- 7 → 1
- 8 → 2
- 9 → 1
- 10 → 2
- 11 → 3

All edges are checked:
* Hub 0 is adjacent to every peripheral node, and none of those nodes uses color 4, so the hub constraint is satisfied.
* Consecutive peripheral nodes alternate between colors 1 and 2, except for the last edge (11‑1) where node 11 uses color 3, which differs from node 1’s color 1. Hence every peripheral edge joins vertices of distinct colors.

Thus the assignment is a valid 4‑coloring of W₁₁.

---

**Proof that a 3‑coloring is impossible**

1. The peripheral vertices 1‑11 form a cycle of length 11, which is odd.
2. An odd cycle requires at least three distinct colors; with only two colors adjacent vertices would repeat a color, contradicting proper coloring.
3. Suppose a 3‑coloring of W₁₁ existed. The peripheral cycle would use exactly three colors (call them A, B, C). Because the cycle length is odd, the color pattern cannot alternate strictly; at least one color must appear twice on the cycle without another occurrence of the third color between them.
4. The hub vertex 0 is adjacent to every peripheral vertex, so it must receive a color distinct from all colors appearing on the cycle.
5. But the cycle already uses all three available colors; there is no fourth color for the hub. Hence a proper 3‑coloring cannot exist.

Therefore, W₁₁ is not 3‑colorable and the above 4‑coloring is minimal.
