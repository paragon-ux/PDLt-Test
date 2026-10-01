Wheel graph W_11 4‑coloring

Node : Color
0 : 4   (central hub)
1 : 1
2 : 2
3 : 3
4 : 1
5 : 2
6 : 3
7 : 1
8 : 2
9 : 3
10: 1
11: 2

Explanation:
- The peripheral odd cycle (nodes 1‑11) is colored with the repeating pattern 1‑2‑3‑1‑2‑3‑1‑2‑3‑1‑2. No two adjacent peripheral nodes share a color because the pattern respects the cycle ordering and the length 11 (odd) means the last edge (11‑1) connects colors 2 and 1, which are different.
- The hub node 0 is adjacent to every peripheral node, which uses only colors {1,2,3}. Assigning hub color 4 guarantees it differs from all its neighbors.
- Hence all adjacency constraints are satisfied with only four colors.

Proof that 3‑coloring is impossible:
The peripheral cycle alone requires at least 3 colors because it is odd. With only three colors available, the hub would have to reuse one of those colors and would then be adjacent to a peripheral node of the same color, violating the coloring rule. Therefore a fourth distinct color is necessary for a proper coloring of W_11.

---
Result IR follows in the fenced JSON block below.
```json
{
  "files": [
    {
      "filename": "coloring.txt",
      "satisfies": [
        "R1"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "Node : Color\n0 : 4   (central hub)\n1 : 1\n2 : 2\n3 : 3\n4 : 1\n5 : 2\n6 : 3\n7 : 1\n8 : 2\n9 : 3\n10: 1\n11: 2"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "Wheel graph W_11 4‑coloring"
      }
    }
  ],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "evidence": {
      "path": "execution://witness"
    },
    "data": {
      "coloring": {
        "0": 4,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 1,
        "5": 2,
        "6": 3,
        "7": 1,
        "8": 2,
        "9": 3,
        "10": 1,
        "11": 2
      }
    },
    "provisional": true
  }
}
```
