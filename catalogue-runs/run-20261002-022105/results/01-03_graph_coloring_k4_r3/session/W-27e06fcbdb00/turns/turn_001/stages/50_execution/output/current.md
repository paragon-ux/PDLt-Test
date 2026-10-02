import json

# Assign colors 1-4 to nodes of W_11
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
    11: 3
}

# Witness containing the coloring and a brief proof argument
witness = {
    "polarity": "positive",
    "data": {
        "coloring": coloring,
        "proof": "The peripheral cycle has length 11 (odd), which requires at least three colors for a proper coloring. The hub node (0) is adjacent to every peripheral node, so it cannot share any of the three colors used on the cycle and thus demands a fourth distinct color. Hence a 3‑coloring is impossible, while the above assignment uses four colors and satisfies all adjacency constraints."
    }
}

print("WITNESS: " + json.dumps(witness))

[host] Witness values are written into the program, not computed; unverified.

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "coloring": {
        "0": 1,
        "1": 2,
        "2": 3,
        "3": 4,
        "4": 2,
        "5": 3,
        "6": 4,
        "7": 2,
        "8": 3,
        "9": 4,
        "10": 2,
        "11": 3
      },
      "proof": "The peripheral cycle has length 11 (odd), which requires at least three colors for a proper coloring. The hub node (0) is adjacent to every peripheral node, so it cannot share any of the three colors used on the cycle and thus demands a fourth distinct color. Hence a 3‑coloring is impossible, while the above assignment uses four colors and satisfies all adjacency constraints."
    },
    "provisional": true
  }
}
```
