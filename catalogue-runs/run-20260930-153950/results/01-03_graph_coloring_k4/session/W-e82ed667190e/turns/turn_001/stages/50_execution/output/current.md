# Wheel graph W_11 4‑coloring and proof of 3‑color impossibility

The wheel graph W₁₁ consists of a central hub node 0 connected to each peripheral node 1‑11, and the peripheral nodes form an odd cycle (11 nodes).

## 4‑coloring
We assign colors from the set {1,2,3,4} as follows (node → color):
```
0: 1
1: 2
2: 3
3: 2
4: 3
5: 2
6: 3
7: 2
8: 3
9: 2
10: 3
11: 4
```
All adjacency constraints are satisfied:
- Node 0 (color 1) is adjacent to every peripheral node, none of which uses color 1.
- The peripheral cycle alternates colors 2 and 3 except for the last edge (11‑1); node 11 uses the fourth color 4, breaking the alternation and avoiding a conflict on edge (11,1).
- No two adjacent peripheral nodes share the same color.

The above coloring can be verified by the accompanying Python script, which checks every edge.

```python
edges = [(0,i) for i in range(1,12)] + [(i,i+1) for i in range(1,11)] + [(11,1)]
coloring = {0:1,1:2,2:3,3:2,4:3,5:2,6:3,7:2,8:3,9:2,10:3,11:4}
for u,v in edges:
    assert coloring[u] != coloring[v], f"Conflict on edge {(u,v)}"
print("All adjacency constraints satisfied.")
```
Running the script yields:
```
All adjacency constraints satisfied.
```

## Proof that a 3‑coloring is impossible
1. The peripheral subgraph is an odd cycle of length 11. Any odd cycle requires **at least three** distinct colors because a 2‑coloring would force an even length.
2. Suppose we colour the cycle with exactly three colors A,B,C. Since the hub node 0 is adjacent to **all** peripheral nodes, its colour must differ from the colour of every peripheral node.
3. But the peripheral cycle already uses three distinct colours; there is no fourth colour available under a 3‑colour regime. Therefore the hub cannot be coloured without creating a conflict.
4. Hence any proper colouring of W₁₁ needs **at least four** colours.

Thus the provided 4‑coloring is optimal.

```json
{
  "files": [
    {
      "filename": "wheel_coloring.py",
      "satisfies": [
        "R1",
        "R2"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "All adjacency constraints satisfied.",
        "observed": "All adjacency constraints satisfied."
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "coloring dict",
        "observed": "0: 1\\n1: 2\\n2: 3\\n3: 2\\n4: 3\\n5: 2\\n6: 3\\n7: 2\\n8: 3\\n9: 2\\n10: 3\\n11: 4"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "Proof that a 3‑coloring is impossible",
        "observed": "Thus any proper colouring of W₁₁ needs **at least four** colours."
      }
    }
  ],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "evidence": {
      "path": "execution://witness",
      "section": null,
      "observed": null
    },
    "data": {
      "coloring": {
        "0": 1,
        "1": 2,
        "2": 3,
        "3": 2,
        "4": 3,
        "5": 2,
        "6": 3,
        "7": 2,
        "8": 3,
        "9": 2,
        "10": 3,
        "11": 4
      }
    },
    "domain": null,
    "provisional": true
  }
}
```
