UNVERIFIED ANSWER: Substantive verification was not completed after repair attempts. Reason: [WITNESS_INVALID] The witness does not check: the WITNESS line printed by the program does not check: Invalid positive witness structure: basis: Extra inputs are not permitted; argument: Extra inputs are not permitted Rule: A witness is valid only if the host's checks confirm it against the task's constraints. Next attempt: Return a witness that satisfies the check named above, or mark the requirement open with the defect recorded.

Attempt 1: WITNESS_INVALID

Candidate deliverable:
Four‑coloring for the wheel graph W₁₁ (nodes 0‑11)

**Color assignment** (using colors 1‑4):
- Node 0 (hub) : **4**
- Peripheral nodes (cycle 1‑11) : repeat the pattern 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2
  - 1 → 1
  - 2 → 2
  - 3 → 3
  - 4 → 1
  - 5 → 2
  - 6 → 3
  - 7 → 1
  - 8 → 2
  - 9 → 3
  - 10 → 1
  - 11 → 2

This assignment respects all adjacency constraints:
- The hub (0) is adjacent to every peripheral node, and it uses color 4 which differs from colors 1‑3 used on the periphery.
- Consecutive peripheral nodes receive distinct colors because the pattern cycles 1‑2‑3‑1‑… and the cycle length (11) is odd, so the last edge (11‑1) connects nodes colored 2 and 1, also distinct.

**Why 3‑coloring is impossible**
The peripheral nodes form an odd cycle (length 11). An odd cycle cannot be properly colored with only two colors; it requires at least three colors to avoid adjacent equal colors. Suppose we attempted a 3‑coloring of the whole wheel using colors A, B, C. The hub must receive a color different from all its neighbours, so it would need a fourth distinct color, contradicting the assumption of only three colors. Hence the wheel W₁₁ is not 3‑colorable; a fourth color is mandatory.

**Python witness program**
The following script verifies the above coloring and prints a JSON witness object.
```python
import json

# Coloring dictionary: node -> color
coloring = {
    0: 4,
    1: 1, 2: 2, 3: 3, 4: 1, 5: 2, 6: 3,
    7: 1, 8: 2, 9: 3, 10: 1, 11: 2,
}

# Edge list of W_11
edges = [(0, i) for i in range(1, 12)] + [(i, i+1) for i in range(1, 11)] + [(11, 1)]

# Verify coloring respects adjacency
valid = all(coloring[u] != coloring[v] for u, v in edges)

witness = {
    "polarity": "positive" if valid else "negative",
    "data": {
        "coloring": coloring,
        "description": "Valid 4‑coloring of W_11" if valid else "Invalid coloring",
    },
    "basis": "proof",
    "argument": "Checked all adjacency constraints programmatically.",
}
print("WITNESS: " + json.dumps(witness))
```
The script confirms the coloring is valid and emits the required witness line.
