# wheel_coloring.py
# 4‑coloring of the wheel graph W_11 (12 nodes: hub 0, outer cycle 1‑11)
# Colors are integers 1‑4. No adjacent vertices share the same color.

# A valid coloring:
# hub (0) = 1
# outer vertices alternate 2,3,4 around the cycle, ensuring the odd length forces use of all three colors.
coloring = {
    0: 1,
    1: 2,
    2: 3,
    3: 4,
    4: 2,
    5: 3,
    6: 4,
    7: 2,
    8: 3,
    9: 4,
    10: 2,
    11: 3,
}

# Output the list of (node, color) pairs
pairs = [(node, coloring[node]) for node in sorted(coloring)]
print(pairs)

# Explanation why 3‑coloring is impossible:
# The outer cycle 1‑11 has odd length (11). Any proper coloring of an odd cycle requires at least 3 colors.
# The hub vertex 0 is adjacent to every outer vertex, so its color must differ from each of the 11 outer colors.
# Since the outer vertices already use all three colors, the hub cannot reuse any of them without creating a conflict.
# Therefore a fourth color is necessary, proving that a 3‑coloring does not exist.

# The script, when run, prints the required coloring list.

```json
{
  "files": [
    {
      "filename": "wheel_coloring.py",
      "satisfies": [
        "R1",
        "R3"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "coloring = {\\n    0: 1,\\n    1: 2,\\n    2: 3,\\n    3: 4,\\n    4: 2,\\n    5: 3,\\n    6: 4,\\n    7: 2,\\n    8: 3,\\n    9: 4,\\n    10: 2,\\n    11: 3,\\n}"
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
        "observed": "coloring = {\\n    0: 1,\\n    1: 2,\\n    2: 3,\\n    3: 4,\\n    4: 2,\\n    5: 3,\\n    6: 4,\\n    7: 2,\\n    8: 3,\\n    9: 4,\\n    10: 2,\\n    11: 3,\\n}"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "# Explanation why 3‑coloring is impossible:\\n# The outer cycle 1‑11 has odd length (11). Any proper coloring of an odd cycle requires at least 3 colors."
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "print(pairs)"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "# Explanation why 3‑coloring is impossible:"
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
      "coloring": [
        [
          0,
          1
        ],
        [
          1,
          2
        ],
        [
          2,
          3
        ],
        [
          3,
          4
        ],
        [
          4,
          2
        ],
        [
          5,
          3
        ],
        [
          6,
          4
        ],
        [
          7,
          2
        ],
        [
          8,
          3
        ],
        [
          9,
          4
        ],
        [
          10,
          2
        ],
        [
          11,
          3
        ]
      ]
    },
    "domain": null,
    "provisional": true
  }
}
```
