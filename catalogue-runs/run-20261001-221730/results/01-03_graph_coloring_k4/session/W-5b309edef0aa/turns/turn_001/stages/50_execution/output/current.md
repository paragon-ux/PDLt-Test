import json

assignment = {
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
proof = ("In the wheel graph W_11 the peripheral nodes form an odd cycle of length 11, "
         "which requires at least three colors. The hub node 0 is adjacent to every peripheral node, "
         "so it must use a color distinct from the colors used on the peripheral nodes. "
         "With only three colors available, the hub would share a color with at least one peripheral node, "
         "contradicting the coloring constraints. Thus a fourth color is necessary, and the assignment above "
         "is a valid 4‑coloring.")
witness = {
    "polarity": "positive",
    "data": {
        "color_assignment": assignment,
        "proof": proof
    }
}
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "color_assignment": {
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
      "proof": "In the wheel graph W_11 the peripheral nodes form an odd cycle of length 11, which requires at least three colors. The hub node 0 is adjacent to every peripheral node, so it must use a color distinct from the colors used on the peripheral nodes. With only three colors available, the hub would share a color with at least one peripheral node, contradicting the coloring constraints. Thus a fourth color is necessary, and the assignment above is a valid 4‑coloring."
    },
    "provisional": false
  }
}
```
