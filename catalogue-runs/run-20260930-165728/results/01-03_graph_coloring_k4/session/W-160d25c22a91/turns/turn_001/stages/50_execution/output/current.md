# 4-coloring of wheel graph W_11
# Nodes: 0 (hub), 1..11 (outer cycle)
# Colors: 1,2,3,4
# Assignment ensures adjacent nodes differ.
coloring = {
    0: 1,
    1: 2,
    2: 3,
    3: 2,
    4: 3,
    5: 2,
    6: 3,
    7: 2,
    8: 3,
    9: 2,
    10: 3,
    11: 4
}

# Verify constraints (hub edges and outer cycle)
def verify(col):
    # hub edges
    for i in range(1,12):
        if col[0] == col[i]:
            return False
    # outer cycle edges
    for i in range(1,12):
        j = i+1 if i<11 else 1
        if col[i] == col[j]:
            return False
    return True

assert verify(coloring), "Coloring invalid"

# Impossibility of 3‑coloring argument (concise textual proof)
proof = (
    "The outer nodes 1..11 form an odd cycle of length 11. "
    "An odd cycle is not 2‑colorable, therefore any proper coloring of the cycle requires at least 3 distinct colors. "
    "The hub node 0 is adjacent to every outer node, so it must use a color different from each of the three colors appearing on the cycle. "
    "Hence a fourth color is mandatory, proving that a 3‑coloring of W_11 is impossible."
)
print("WITNESS:", {"polarity":"positive","evidence":{"path":"execution://witness"},"data":{"coloring":coloring,"proof":proof}})

```json
{
  "files": [
    {
      "filename": "coloring.py",
      "satisfies": [
        "R1",
        "R2",
        "R3"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "coloring = {\\n    0: 1,\\n    1: 2,\\n    2: 3,\\n    3: 2,\\n    4: 3,\\n    5: 2,\\n    6: 3,\\n    7: 2,\\n    8: 3,\\n    9: 2,\\n    10: 3,\\n    11: 4\\n}"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "coloring = {\\n    0: 1,\\n    1: 2,\\n    2: 3,\\n    3: 2,\\n    4: 3,\\n    5: 2,\\n    6: 3,\\n    7: 2,\\n    8: 3,\\n    9: 2,\\n    10: 3,\\n    11: 4\\n}"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "proof = (\\n    \\\"The outer nodes 1..11 form an odd cycle of length 11. \\\"\\n    \\\"An odd cycle is not 2‑colorable, therefore any proper coloring of the cycle requires at least 3 distinct colors. \\\"\\n    \\\"The hub node 0 is adjacent to every outer node, so it must use a color different from each of the three colors appearing on the cycle. \\\"\\n    \\\"Hence a fourth color is mandatory, proving that a 3‑coloring of W_11 is impossible.\\\"\\n)"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "# 4-coloring of wheel graph W_11\\n# Nodes: 0 (hub), 1..11 (outer cycle)\\n# Colors: 1,2,3,4\\n# Assignment ensures adjacent nodes differ."
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
      },
      "proof": "The outer nodes 1..11 form an odd cycle of length 11. An odd cycle is not 2‑colorable, therefore any proper coloring of the cycle requires at least 3 distinct colors. The hub node 0 is adjacent to every outer node, so it must use a color different from each of the three colors appearing on the cycle. Hence a fourth color is mandatory, proving that a 3‑coloring of W_11 is impossible."
    },
    "provisional": false
  }
}
```
