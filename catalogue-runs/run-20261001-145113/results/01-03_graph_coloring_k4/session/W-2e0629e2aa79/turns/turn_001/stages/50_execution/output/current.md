import json

coloring = {
    0: 4,
    1: 1,
    2: 2,
    3: 3,
    4: 1,
    5: 2,
    6: 3,
    7: 1,
    8: 2,
    9: 3,
    10: 1,
    11: 2
}

proof = ("Because the peripheral cycle of 11 nodes is odd, it cannot be 2-colored; "
         "thus it requires at least three colors. In any proper 3-coloring of the peripheral cycle, "
         "all three colors are used. The hub node is adjacent to every peripheral node, "
         "so it cannot use any of those three colors, requiring a fourth distinct color. "
         "Therefore the wheel graph W_11 needs at least four colors, and the above assignment "
         "provides a valid 4-coloring.")

result = {
    "polarity": "positive",
    "data": {
        "coloring": coloring,
        "proof": proof
    }
}

print("WITNESS: " + json.dumps(result))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
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
      },
      "proof": "Because the peripheral cycle of 11 nodes is odd, it cannot be 2-colored; thus it requires at least three colors. In any proper 3-coloring of the peripheral cycle, all three colors are used. The hub node is adjacent to every peripheral node, so it cannot use any of those three colors, requiring a fourth distinct color. Therefore the wheel graph W_11 needs at least four colors, and the above assignment provides a valid 4-coloring."
    },
    "provisional": false
  }
}
```
